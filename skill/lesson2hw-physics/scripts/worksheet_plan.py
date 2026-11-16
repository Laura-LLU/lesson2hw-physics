"""Check explicit counts, estimated duration and host-reviewed teaching boundaries.

This module validates recorded reviews, not the semantic truth of an Agent's review.
Estimates are teacher heuristics, not official paper timings or student measurements.
"""
import math

def estimate_minutes(course,level,rows):
    mcq_rate=1.25 if course=='0625' else 1.5
    sq_rate=1.8 if course=='9702' and level=='AS' else 1.5
    if any(r.get('marks') is None for r in rows):raise ValueError('Cannot estimate duration with unknown marks')
    return round(sum(mcq_rate if r['kind']=='mcq' else sq_rate*r['marks'] for r in rows),2)

def validate_review(course,level,rows,review):
    if review.get('course')!=course or review.get('level')!=level:raise ValueError('Teaching review belongs to a different course/level')
    scope=review.get('scope',{})
    if not scope.get('include') or 'exclude' not in scope:raise ValueError('Record included and excluded teaching scope')
    checks=review.get('questions',{})
    for row in rows:
        q=checks.get(row['id'],{})
        if q.get('scope_pass') is not True or q.get('answer_checked') is not True or q.get('already_taught') is not False:
            raise ValueError('Missing scope/answer/duplicate review: '+row['id'])
        if any(p.get('confirmed') is not True for p in q.get('prerequisites',[])):
            raise ValueError('Unconfirmed prerequisite: '+row['id'])
        if not q.get('reason'):raise ValueError('Record a question-specific scope reason: '+row['id'])
        if row.get('excerpt') and q.get('independently_answerable') is not True:
            raise ValueError('Excerpt needs an independent-answerability review: '+row['id'])
    req=review.get('requirements',{});failures=[]
    counts={k:sum(r['kind']==k for r in rows) for k in ['mcq','structured']}
    for kind,number in req.get('counts',{}).items():
        if kind not in counts or type(number) is not int or number<0:raise ValueError('Invalid requested question count')
        if counts[kind]!=number:failures.append(f'{kind}: requested {number}, selected {counts[kind]}')
    if req.get('mixed') and not all(counts.values()):failures.append('Mixed request needs both MCQ and structured questions')
    if req.get('whole_questions_only') and any(r.get('excerpt') for r in rows):failures.append('Complete original questions requested; excerpts cannot substitute')
    estimated=estimate_minutes(course,level,rows)
    minutes=req.get('minutes')
    if minutes is not None:
        if type(minutes) not in (int,float) or not math.isfinite(minutes) or minutes<=0:raise ValueError('Invalid requested duration')
        if abs(estimated-minutes)>minutes*.10:failures.append(f'Estimated {estimated:g} minutes outside target {minutes:g} +/-10%')
    section_estimates={}
    for kind,target in req.get('minutes_by_kind',{}).items():
        if kind not in counts or type(target) not in (int,float) or not math.isfinite(target) or target<=0:raise ValueError('Invalid section duration')
        section_estimates[kind]=estimate_minutes(course,level,[r for r in rows if r['kind']==kind])
        if abs(section_estimates[kind]-target)>target*.10:failures.append(f'{kind}: estimated {section_estimates[kind]:g} minutes outside target {target:g} +/-10%')
    return {'passed':not failures,'counts':counts,'section_estimated_minutes':section_estimates,'complete_original_structured':sum(r['kind']=='structured' and not r.get('excerpt') for r in rows),'excerpt_groups':sum(bool(r.get('excerpt')) for r in rows),'estimated_minutes':estimated,'requested_minutes':minutes,'duration_tolerance':.10,'failures':failures,'estimate_is_heuristic':True,'scope_truth_requires_visual_review':True}

def choose_plan(course,level,rows,review):
    """Select only already-reviewed candidates; never expand the lesson boundary."""
    eligible=[]
    for r in rows:
        try:validate_review(course,level,[r],{**review,'requirements':{}})
        except ValueError:continue
        if review.get('requirements',{}).get('whole_questions_only') and r.get('excerpt'):continue
        eligible.append(r)
    req=review.get('requirements',{});target=req.get('minutes') or sum(req.get('minutes_by_kind',{}).values())
    if not target:
        wanted=req.get('counts',{});chosen=[]
        for kind in ['mcq','structured']:
            pool=[r for r in eligible if r['kind']==kind]
            chosen+=pool[:wanted.get(kind,0)]
        return chosen,validate_review(course,level,chosen,review)
    # Quarter-minute states preserve the exported timing model without rounding drift.
    cap=math.ceil(target*1.1*20);states={(0,0,0):[]}
    for index,r in enumerate(eligible):
        cost=round(estimate_minutes(course,level,[r])*20)
        for (mcq,sq,t),indices in list(states.items()):
            m=mcq+(r['kind']=='mcq');s=sq+(r['kind']=='structured');n=t+cost
            if m>min(40,req.get('counts',{}).get('mcq',40)) or s>min(10,req.get('counts',{}).get('structured',10)) or n>cap:continue
            states.setdefault((m,s,n),indices+[index])
    valid=[]
    for (m,s,t),indices in states.items():
        if req.get('mixed') and not(m and s):continue
        if any((m if k=='mcq' else s)!=v for k,v in req.get('counts',{}).items()):continue
        section_times={'mcq':m*(1.25 if course=='0625' else 1.5),'structured':t/20-m*(1.25 if course=='0625' else 1.5)}
        if any(abs(section_times[k]-v)>v*.10+1e-8 for k,v in req.get('minutes_by_kind',{}).items()):continue
        if abs(t/20-target)>target*.1+1e-8:continue
        section_error=sum(abs(section_times[k]-v) for k,v in req.get('minutes_by_kind',{}).items())
        valid.append((section_error,abs(t-target*20),len(indices),indices))
    if not valid:return [],{'passed':False,'failures':['No reviewed selection meets requested counts/time'],'estimate_is_heuristic':True}
    _,_,_,indices=min(valid);chosen=[eligible[i] for i in indices]
    return chosen,validate_review(course,level,chosen,review)


def validate_reviewed_assets(rows,review):
    """Bind the semantic review to the exact question and answer files exported."""
    import hashlib
    from pathlib import Path
    for row in rows:
        for side in ['question','answer']:
            expected=review['questions'][row['id']].get(side+'_sha256')
            actual=hashlib.sha256(Path(row[side+'_image']).read_bytes()).hexdigest()
            if not expected or expected!=actual:raise ValueError('Reviewed '+side+' image missing or changed: '+row['id'])
