"""Bounded, timed lesson-to-homework workflow shared by all supported topics."""
from pathlib import Path
import argparse,json,time,datetime,hashlib,subprocess,sys,os,uuid,copy

HERE=Path(__file__).resolve().parent

def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(path,data):Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2))
def emit(value):print(json.dumps(value,ensure_ascii=False,indent=2))

def load_job(path):
    path=Path(path).resolve();job=read(path)
    if job.get('schema')!=1:raise ValueError('Unsupported fast job')
    return path,job

def elapsed(job):return max(time.time()-job['received_at_epoch'],time.monotonic()-job['began_at_monotonic'])
def event(job,name,**details):job['events'].append({'stage':name,'at':stamp(),'elapsed_seconds':round(elapsed(job),3),**details})
def budget(job):
    left=job['budget_seconds']-elapsed(job)
    if left<=0:raise RuntimeError('Workflow deadline exceeded; report the actual time and incomplete delivery, never reset the intake clock')
    return left

def run(args,job):
    result=subprocess.run(args,capture_output=True,text=True,timeout=max(1,budget(job)),env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    if result.returncode:raise RuntimeError(result.stderr or result.stdout)
    budget(job);return result.stdout

def make_pairs(rows,dest):
    from material_layout import guides
    from PIL import Image,ImageDraw
    output=[];dest=Path(dest);dest.mkdir(exist_ok=True)
    for r in rows:
        q=Image.open(r['question_image']).convert('RGB');a=Image.open(r['answer_image']).convert('RGB')
        q.thumbnail((1100,1000000));a.thumbnail((1100,1000000))
        if r['kind']=='mcq':
            image=Image.new('RGB',(max(q.width,a.width),q.height+a.height+80),'white');draw=ImageDraw.Draw(image)
            draw.text((8,6),r['id']+' | QUESTION',fill='black');image.paste(q,(0,30));draw.text((8,q.height+40),'PAIRED ANSWER',fill='black');image.paste(a,(0,q.height+70))
        else:
            image=Image.new('RGB',(q.width+a.width+30,max(q.height,a.height)+45),'white');draw=ImageDraw.Draw(image)
            draw.text((8,6),r['id']+' | QUESTION',fill='black');draw.text((q.width+20,6),'PAIRED ANSWER',fill='black');image.paste(q,(0,35));image.paste(a,(q.width+30,35))
        tiles=[]
        for n,top in enumerate(range(0,image.height,1720),1):
            target=dest/(r['id']+'-part'+str(n)+'.jpg');image.crop((0,max(0,top-80),image.width,min(image.height,top+1800))).save(target,quality=93);tiles.append(str(target))
        target=Path(tiles[0]);output.append({'id':r['id'],'pair_preview':str(target),'pair_previews':tiles,'question_image':r['question_image'],'answer_image':r['answer_image'],'question_sha256':sha(r['question_image']),'answer_sha256':sha(r['answer_image']),'marks':r['marks'],'source_ref':r['source_ref'],'excerpt':r.get('excerpt',False),'layout_review_needed':[side for side in ['question','answer'] if sha(r[side+'_image']) not in guides()]})
    return output

def pack_previews(pairs,dest):
    from PIL import Image
    batches=[];pending=[];height=0
    def flush():
        nonlocal pending,height
        if not pending:return
        if len(pending)==1:batches.append(pending[0]['pair_preview'])
        else:
            images=[Image.open(p['pair_preview']).convert('RGB') for p in pending];sheet=Image.new('RGB',(max(i.width for i in images),sum(i.height for i in images)+16*(len(images)-1)),'#e6edf2');y=0
            for image in images:sheet.paste(image,(0,y));y+=image.height+16
            target=Path(dest)/('batch-'+str(len(batches)+1)+'.jpg');sheet.save(target,quality=93);batches.append(str(target))
        pending=[];height=0
    flattened=[{'pair_preview':file} for pair in pairs for file in pair.get('pair_previews',[pair['pair_preview']])]
    for p in flattened:
        with Image.open(p['pair_preview']) as opened:h=opened.height
        if pending and height+h+16>1800:flush()
        pending.append(p);height+=h+16
    flush();return batches

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--workspace',default=os.environ.get('PHYSICS_HOME',str(Path.home()/'codex/lesson2hw-physics')))
    sub=ap.add_subparsers(dest='cmd',required=True)
    begin=sub.add_parser('begin');begin.add_argument('--material',action='append');begin.add_argument('--pages');begin.add_argument('--request',required=True);begin.add_argument('--receipt-file')
    for name in ['input','status','candidates','fetch','build','finish','scope','excerpt','prepare','compose','abort']:
        p=sub.add_parser(name);p.add_argument('--job',required=True)
        if name=='prepare':p.add_argument('--scope-file',required=True)
        if name=='compose':p.add_argument('--assessment-file',required=True);p.add_argument('--title',required=True)
        if name=='abort':p.add_argument('--reason',required=True)
        if name=='scope':p.add_argument('--file',required=True)
        if name=='excerpt':p.add_argument('--from-id',required=True);p.add_argument('--spec-file',required=True)
        if name=='candidates':p.add_argument('--kind',choices=['mcq','structured']);p.add_argument('--limit',type=int,default=8)
        if name=='fetch':p.add_argument('ids',nargs='+')
        if name=='build':p.add_argument('--review-file',required=True);p.add_argument('--title',required=True);p.add_argument('ids',nargs='+')
        if name=='finish':p.add_argument('--visual-reviewed',action='store_true');p.add_argument('--delivery-note',required=True)
    sub.add_parser('coverage')
    args=ap.parse_args();workspace=Path(args.workspace).expanduser().resolve()
    if args.cmd=='begin':
        started=time.time();mono=time.monotonic();inputs=[{'path':str(Path(x).expanduser().resolve()),'sha256':sha(Path(x).expanduser())} for x in (args.material or [])]
        receipt=read(args.receipt_file) if args.receipt_file else None
        if receipt:
            if set(receipt['input_sha256'])!={i['sha256'] for i in inputs}:raise ValueError('Upload receipt does not match lesson files')
            started=receipt['received_at_epoch']
            if started>time.time()+1:raise ValueError('Upload receipt is in the future')
        path=workspace/'jobs'/('lesson-'+uuid.uuid4().hex[:12])/'job.json';path.parent.mkdir(parents=True)
        if not inputs:
            textfile=path.parent/'teacher-request.txt';textfile.write_text(args.request);inputs=[{'path':str(textfile),'sha256':sha(textfile)}]
        job={'schema':1,'job_id':path.parent.name,'received_at':datetime.datetime.fromtimestamp(started,datetime.timezone.utc).isoformat(),'received_at_epoch':started,'began_at_monotonic':mono,'target_seconds':300,'budget_seconds':600,'request':args.request,'inputs':inputs,'pages':args.pages,'workspace':str(workspace),'events':[],'candidate_rounds':{},'candidate_ids':[],'fetched_ids':[],'status':'received','timing_includes_pre_job_wait':bool(receipt)}
        event(job,'material_received');save(path,job);budget(job)
        from input_cache import prepare
        previews=[prepare(i['path'],workspace/'lesson-cache',job.get('pages'),timeout_seconds=budget(job)) for i in inputs]
        job['input_previews']=previews;event(job,'input_prepared');save(path,job)
        emit({'job':str(path),'input_sha256':[i['sha256'] for i in inputs],'inputs':previews,'remaining_seconds':round(budget(job),1),'next':'Read these previews, then prepare --scope-file'});return
    from homework import load_bank,allowed
    if args.cmd=='coverage':
        from retrieval import coverage
        data=coverage({c:load_bank(workspace,c) for c in ['9702','0625']});emit({'theory_topics':data,'practical_papers':{'9702':['3','5'],'0625_P6':'no built-in materials; not counted as end-to-end verified'},'all_topics_semantically_tested':False});return
    path,job=load_job(args.job)
    if args.cmd=='abort':
        job['status']='failed';job['under_five_minutes']=False;event(job,'operator_aborted',reason=args.reason);save(path,job);emit({'status':'failed','elapsed_seconds':round(elapsed(job),3),'reason':args.reason});return
    if args.cmd=='status':emit({'job':str(path),'status':job['status'],'elapsed_seconds':round(elapsed(job),2),'remaining_seconds':max(0,round(job['budget_seconds']-elapsed(job),2)),'events':job['events']});return
    try:
        budget(job)
        if args.cmd=='input':
            from input_cache import prepare
            previews=[prepare(i['path'],workspace/'lesson-cache',job.get('pages'),timeout_seconds=budget(job)) for i in job['inputs']]
            job['input_previews']=previews;event(job,'input_prepared');save(path,job);emit({'job':str(path),'inputs':previews,'remaining_seconds':round(budget(job),1)});return
        if args.cmd=='scope':
            scope=read(args.file)
            for key in ['course','level','include','exclude','query','topics']:
                if key not in scope:raise ValueError('Missing scope field: '+key)
            allowed(scope['course'],scope['level'])
            if scope.get('input_visually_reviewed') is not True:raise ValueError('Read the actual lesson previews before recording scope')
            if scope.get('input_sha256')!=[i['sha256'] for i in job['inputs']]:raise ValueError('Scope not bound to these lesson files')
            job['scope']=scope;job['status']='scope_reviewed';event(job,'lesson_scope_reviewed');save(path,job);emit({'remaining_seconds':round(budget(job),1),'next':'candidates (metadata/text only); fetch only the bounded shortlist'});return
        if args.cmd=='prepare':
            def child(command):return json.loads(run([sys.executable,'-B',str(HERE/'fast.py'),'--workspace',str(workspace),*command,'--job',str(path)],job))
            child(['scope','--file',args.scope_file]);path,job=load_job(path);scope=job['scope'];req=scope.get('requirements',{})
            if scope['course']=='0625' and scope['level']=='P6':raise ValueError('0625 Paper 6 has no built-in assets; import valid P6 material, never use P5')
            targets=req.get('minutes_by_kind',{});counts=req.get('counts',{});kinds=list(dict.fromkeys([*counts,*targets]))
            if not kinds:kinds=['mcq','structured'] if req.get('mixed') else ['structured']
            summaries=[];ids=[]
            for kind in kinds:
                if kind not in ('mcq','structured'):raise ValueError('Invalid question kind')
                n=counts.get(kind)
                if n==0:continue
                if n is None:
                    minutes=targets.get(kind,req.get('minutes',30)/len(kinds))
                    n=round(minutes/(1.25 if scope['course']=='0625' else 1.5)) if kind=='mcq' else max(1,round(minutes/12))
                limit=min(24,max(1,n+2));result=child(['candidates','--kind',kind,'--limit',str(limit)])
                for r in result['candidates']:
                    summaries.append({k:r[k] for k in ['id','marks','kind','source_ref','possible_cross_scope_terms']});ids.append(r['id'])
            if not ids:raise ValueError('No matching candidates; record a coverage gap instead of widening taught scope')
            media=child(['fetch',*ids]);emit({'job':str(path),'candidates':summaries,'previews_to_read':media['previews_to_read'],'layout_review_needed':{p['id']:p['layout_review_needed'] for p in media['pairs'] if p['layout_review_needed']},'remaining_seconds':media['remaining_seconds'],'next':'Inspect paired previews, record assessment, then compose. No extra reference files needed for normal cases.'});return
        if args.cmd=='compose':
            assessment=read(args.assessment_file);scope=job['scope'];checks=assessment.get('questions',{});snapshots=job.get('preview_assets',{})
            if assessment.get('input_sha256')!=[i['sha256'] for i in job['inputs']]:raise ValueError('Assessment must be bound to the viewed lesson')
            for ident,check in checks.items():
                if ident not in snapshots:raise ValueError('No question/answer preview snapshot for '+ident)
                row=job['fetched_rows'][ident]
                for side in ['question','answer']:
                    digest=snapshots[ident][side+'_sha256']
                    if sha(row[side+'_image'])!=digest:raise ValueError('Asset changed after preview: '+ident)
                    check[side+'_sha256']=digest
                    if side+'_layout' in check:check[side+'_layout']['sha256']=digest
            review={'course':scope['course'],'level':scope['level'],'input_sha256':assessment['input_sha256'],'scope':{'include':scope['include'],'exclude':scope['exclude']},'requirements':scope.get('requirements',{}),'questions':checks}
            from worksheet_plan import choose_plan
            pool=[job['fetched_rows'][i] for i in checks];chosen,verification=choose_plan(scope['course'],scope['level'],pool,review)
            if not verification['passed']:raise ValueError('Reviewed pool cannot satisfy request: '+'; '.join(verification['failures']))
            reviewfile=path.parent/'review.json';save(reviewfile,review)
            result=json.loads(run([sys.executable,'-B',str(HERE/'fast.py'),'--workspace',str(workspace),'build','--job',str(path),'--review-file',str(reviewfile),'--title',args.title,*[r['id'] for r in chosen]],job));emit({**result,'selected_ids':[r['id'] for r in chosen],'requirements_check':verification});return
        scope=job['scope'];course=scope['course'];rows=load_bank(workspace,course)
        os.environ['LESSON2HW_DEADLINE_EPOCH']=str(job['received_at_epoch']+job['budget_seconds'])
        if args.cmd=='candidates':
            from retrieval import shortlist
            kind=args.kind or 'all';rounds=job['candidate_rounds'].get(kind,0)
            if rounds>=2:raise ValueError('At most two shortlist rounds per kind; do not expand into an unbounded library scan')
            used=set(scope.get('exclude_ids',[]))
            history=workspace/course/'history.jsonl'
            if history.is_file() and not scope.get('include_used'):
                for line in history.read_text().splitlines():
                    previous=json.loads(line);used.update(previous.get('ids',[]));used.update(x.get('original_id') for x in previous.get('excerpt_details',[]) if x.get('original_id'))
            result=shortlist(workspace,course,rows,{**scope,'seen_candidate_ids':job['candidate_ids']},args.kind,args.limit,used)
            job['candidate_rounds'][kind]=rounds+1;job['candidate_ids']=list(dict.fromkeys(job['candidate_ids']+[r['id'] for r in result['candidates']]))
            if len(job['candidate_ids'])>48:raise ValueError('Too many candidates for this timed request; refine scope before downloading')
            event(job,'candidates_retrieved',kind=kind,count=len(result['candidates']),media_downloaded=0);save(path,job);emit({**result,'remaining_seconds':round(budget(job),1)});return
        if args.cmd=='fetch':
            if len(set(args.ids))!=len(args.ids) or not set(args.ids).issubset(job['candidate_ids']):raise ValueError('Fetch only IDs from this job shortlist')
            if len(set(job['fetched_ids']+args.ids))>32:raise ValueError('Media budget exceeded; do not bulk-download candidates')
            from builtin_bank import ensure_assets
            from excerpts import get_recipe,materialize
            lookup={r['id']:r for r in rows};lookup.update(job.get('fetched_rows',{}));selected=[]
            for ident in args.ids:
                recipe=get_recipe(ident,workspace,course)
                selected.append(materialize(workspace,recipe,lookup[recipe['original_id']]) if recipe else lookup[ident])
            ensure_assets(selected)
            for r in selected:lookup[r['id']]=r
            # Job-local index keeps cached bank and homework history untouched.
            bank=path.parent/'bank'/course/'bank.json';bank.parent.mkdir(parents=True,exist_ok=True);save(bank,{'course':course,'questions':list(lookup.values())})
            job['fetched_rows']={**job.get('fetched_rows',{}),**{r['id']:r for r in selected}};job['fetched_ids']=list(dict.fromkeys(job['fetched_ids']+args.ids))
            pairs=make_pairs(selected,path.parent/'candidate-pairs');job['preview_assets']={**job.get('preview_assets',{}),**{p['id']:{k:p[k] for k in ['question_sha256','answer_sha256']} for p in pairs}};batches=pack_previews(pairs,path.parent/'candidate-pairs');event(job,'candidate_media_prepared',count=len(selected));save(path,job);emit({'previews_to_read':batches,'pairs':pairs,'remaining_seconds':round(budget(job),1)});return
        if args.cmd=='excerpt':
            if args.from_id not in job['fetched_ids']:raise ValueError('Read/fetch the parent question and answer before excerpting')
            parent=job['fetched_rows'][args.from_id]
            if parent['kind']!='structured' or parent.get('excerpt'):raise ValueError('Create structured subparts from a whole original question')
            spec=read(args.spec_file)
            if spec.get('independently_answerable_reviewed') is not True or not spec.get('retained_parts') or not spec.get('retrieval_text'):raise ValueError('Record retained parts, retrieval description and independent answerability')
            if type(spec.get('marks')) is not int or spec['marks']<1 or (parent.get('marks') and spec['marks']>parent['marks']):raise ValueError('Use the actual retained mark total')
            recipe={**spec,'course':course,'original_id':parent['id'],'source_ref':parent['source_ref']+' ('+spec['retained_parts']+') [excerpt]','excerpt':True,'topics':parent['topics'],'subtopics':parent['subtopics'],'difficulty':parent['difficulty'],'review_version':'0.5.8'}
            from excerpts import materialize
            row=materialize(workspace,recipe,parent)
            for side in ['question','answer']:recipe[side+'_output_sha256']=sha(row[side+'_image'])
            folder=workspace/course/'reviewed-excerpt-recipes';folder.mkdir(exist_ok=True)
            destination=folder/(recipe['id']+'.json')
            if destination.exists() and read(destination)!=recipe:raise ValueError('Existing recipe differs; use a new versioned ID')
            save(destination,recipe);job['fetched_rows'][row['id']]=row;job['fetched_ids']=list(dict.fromkeys(job['fetched_ids']+[row['id']]))
            bank=path.parent/'bank'/course/'bank.json';data=read(bank);data['questions']=[r for r in data['questions'] if r['id']!=row['id']]+[row];save(bank,data)
            pairs=make_pairs([row],path.parent/'candidate-pairs');job.setdefault('preview_assets',{})[row['id']]={k:pairs[0][k] for k in ['question_sha256','answer_sha256']};event(job,'new_independent_excerpt_saved',id=row['id'],marks=row['marks']);save(path,job)
            emit({'pairs':pairs,'recipe_saved':True,'remaining_seconds':round(budget(job),1),'next':'Review the actual retained question and answer, then include this ID in build'});return
        if args.cmd=='build':
            fingerprint=hashlib.sha256(json.dumps({'review':read(args.review_file),'title':args.title,'ids':args.ids},sort_keys=True,ensure_ascii=False).encode()).hexdigest()
            if job.get('build_fingerprint')==fingerprint and job.get('outputs') and job.get('qa_contacts') and all(Path(v).is_file() for v in job['outputs'].values()):
                from worksheet_plan import validate_reviewed_assets
                validate_reviewed_assets([job['fetched_rows'][i] for i in args.ids],read(args.review_file))
                job['status']='awaiting_visual_review';save(path,job);emit({'outputs':job['outputs'],'contact_sheets':job['qa_contacts'],'warnings':[w for r in read(job['qa_report']) for w in r['warnings']],'remaining_seconds':round(budget(job),1),'idempotent_replay':True,'next':'Inspect current contact sheets, then finish; do not compose again unless the review changed'});return
            if not set(args.ids).issubset(job['fetched_ids']):raise ValueError('Build only fetched/reviewed question IDs')
            review=read(args.review_file)
            if review.get('input_sha256')!=[i['sha256'] for i in job['inputs']]:raise ValueError('Question review is not bound to this material intake')
            if review.get('course')!=course or review.get('level')!=scope['level']:raise ValueError('Review belongs to a different course/level')
            if review.get('requirements',{})!=scope.get('requirements',{}):raise ValueError('Do not silently change requested counts or times')
            from worksheet_plan import validate_review,validate_reviewed_assets
            selected=[job['fetched_rows'][i] for i in args.ids];check=validate_review(course,scope['level'],selected,review)
            if not check['passed']:raise ValueError('Teacher requirements failed: '+'; '.join(check['failures']))
            validate_reviewed_assets(selected,review);event(job,'retained_question_and_answer_reviewed',question_count=len(selected));save(path,job)
            from retrieval import duplicate_pairs
            duplicates=duplicate_pairs(selected)
            if duplicates:raise ValueError('Duplicate question bodies in this worksheet: '+str(duplicates))
            from material_layout import guides
            for row in selected:
                for side in ['question','answer']:
                    check=review['questions'][row['id']]
                    if sha(row[side+'_image']) not in guides() and side+'_layout' not in check:
                        raise ValueError('Unreviewed source geometry: '+row['id']+' '+side+'; inspect original numbering, figures/captions and provide '+side+'_layout')
            revision=job.get('build_revision',0)+1;job['build_revision']=revision
            output=path.parent/('output' if revision==1 else 'output-v'+str(revision));save(path,job)
            command=[sys.executable,'-B',str(HERE/'homework.py'),'--workspace',str(path.parent/'bank'),'export','--course',course,'--level',scope['level'],'--year',str(scope.get('syllabus_year',2026)),'--checked','--review-file',str(Path(args.review_file).resolve()),'--title',args.title,'--output-dir',str(output)]
            if scope.get('requirements',{}).get('minutes'):command+=['--time-limit',str(scope['requirements']['minutes'])]
            command+=args.ids;paths=json.loads(run(command,job));job['outputs']=paths;job['selected_ids']=args.ids;job['requirements_check']=check;event(job,'paired_pdf_generated')
            report=run([sys.executable,'-B',str(HERE/'qa_pdf.py'),paths['student'],paths['answers'],'--output-dir',str(output/'qa'),'--contact-only'],job).strip()
            qa=read(report);job['qa_pdf_sha256']={k:sha(v) for k,v in paths.items()};job['qa_report']=report;job['qa_contacts']=[r['contact_sheet'] for r in qa];event(job,'all_pages_rendered');job['status']='awaiting_visual_review';job['build_fingerprint']=fingerprint;save(path,job)
            emit({'outputs':paths,'contact_sheets':job['qa_contacts'],'warnings':[w for r in qa for w in r['warnings']],'remaining_seconds':round(budget(job),1),'next':'Inspect all contact sheets and actual retained content; finish only after visual acceptance'});return
        if args.cmd=='finish':
            if job['status']!='awaiting_visual_review' or not args.visual_reviewed:raise ValueError('Generate and visually inspect both PDFs before delivery')
            if not args.delivery_note.strip():raise ValueError('Record visual review result and delivery destination')
            if any(sha(i['path'])!=i['sha256'] for i in job['inputs']):raise ValueError('Lesson source changed during the run')
            if any(sha(v)!=job.get('qa_pdf_sha256',{}).get(k) for k,v in job['outputs'].items()):raise ValueError('Outputs changed after QA rendering; render and inspect again')
            if any(len(r.get('question_labels',[]))!=len(job['selected_ids']) for r in read(job['qa_report'])):raise ValueError('PDF question count does not match selected groups')
            if any(r['warnings'] for r in read(job['qa_report'])):raise ValueError('Resolve PDF QA warnings before delivery')
            event(job,'visual_review_complete',note=args.delivery_note);job['elapsed_seconds']=round(elapsed(job),3);job['status']='delivery_ready';job['under_five_minutes']=job['elapsed_seconds']<=300;job['output_sha256']={k:sha(v) for k,v in job['outputs'].items()};job['page_counts']={Path(r['pdf']).name:r['pages'] for r in read(job['qa_report'])};save(path,job)
            emit({'status':job['status'],'elapsed_seconds':job['elapsed_seconds'],'under_five_minutes':job['under_five_minutes'],'under_ten_minutes':job['elapsed_seconds']<600,'outputs':job['outputs'],'page_counts':job['page_counts'],'counts':job['requirements_check']['counts'],'estimated_minutes':job['requirements_check']['estimated_minutes'],'timing_scope':'Receipt to reviewed artifacts ready. Actual client delivery must additionally be observed; script-only timing is not an Agent end-to-end pass.'});return
    except Exception as exc:
        path,job=load_job(path)
        job['status']='failed';event(job,'failed',reason=str(exc));save(path,job);raise

if __name__=='__main__':
    try:main()
    except (ValueError,RuntimeError,KeyError,FileNotFoundError,subprocess.TimeoutExpired) as exc:raise SystemExit(str(exc))
