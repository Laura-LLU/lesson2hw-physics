"""Bounded full-text retrieval. Never downloads media or declares semantic approval."""
from pathlib import Path
import gzip,hashlib,json,re,sqlite3,math

RES=Path(__file__).resolve().parents[1]/'resources'
STOP=set('a an and are as at be by for from how if in into is it of on or that the their then this to was what when which with calculate state determine explain describe show suggest'.split())

def corpus():return json.loads(gzip.decompress((RES/'retrieval-texts.json.gz').read_bytes()))['items']

def row_text(row,texts):
    item=texts.get(row['id']);asset=row.get('question_asset','')
    if item and ('v='+item['question_sha_prefix']) in asset:return item['text']
    return row.get('search_text','') or ' '.join(row.get('keywords',[]))

def signature(rows):
    material=[{k:r.get(k) for k in ['id','paper','topics','subtopics','search_text','question_asset','answer_asset','marks']} for r in rows]
    return hashlib.sha256((RES/'retrieval-texts.json.gz').read_bytes()+json.dumps(material,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def ensure_fts(workspace,course,rows):
    dest=Path(workspace)/course/'retrieval.sqlite3';dest.parent.mkdir(parents=True,exist_ok=True)
    sig=signature(rows)
    if dest.exists():
        db=sqlite3.connect(dest)
        try:
            if db.execute('select signature from build').fetchone()[0]==sig:return db
        except sqlite3.DatabaseError:pass
        db.close()
    # A failed rebuild never destroys the previous search index.
    db=sqlite3.connect(dest)
    try:
        db.executescript('create table if not exists build(signature text); create virtual table if not exists question_fts using fts5(id UNINDEXED, tags, body, tokenize="unicode61"); ')
        db.execute('begin immediate');db.execute('delete from build');db.execute('delete from question_fts')
        texts=corpus()
        db.executemany('insert into question_fts(id,tags,body) values(?,?,?)',[(r['id'],' '.join(r.get('topics',[])+r.get('subtopics',[])+r.get('keywords',[])),row_text(r,texts)) for r in rows])
        db.execute('insert into build values(?)',(sig,));db.commit();db.close()
    except Exception:
        db.rollback();db.close();raise
    return sqlite3.connect(dest)

def code(label):
    m=re.match(r'(?:Topic\s*)?(\d+(?:\.\d+|[A-Z])?)',label,re.I)
    return m[1] if m else None

def tokens(query):return list(dict.fromkeys(t.lower() for t in re.findall(r'[\w]+',query,flags=re.UNICODE) if t.lower() not in STOP and len(t)>1))[:24]

def canonical_body(text,row=None):
    # Strip index labels and source furniture, retain physical numbers and symbols.
    for label in (row or {}).get('topics',[])+(row or {}).get('subtopics',[]):text=text.replace(label,' ')
    text=re.sub(r'^\s*\d+\s+','',text)
    text=re.sub(r'\s+\d*\s*\[?Turn over.*$','',text,flags=re.I)
    return ''.join(re.findall(r'[a-z0-9]+',text.lower()))

def fingerprint(text,row=None):return hashlib.sha256(canonical_body(text,row).encode()).hexdigest()

def duplicate_pairs(rows):
    texts=corpus();seen={};pairs=[]
    for row in rows:
        text=row_text(row,texts)
        if len(text)<50:continue
        key=fingerprint(text,row)
        if key in seen:pairs.append([seen[key],row['id']])
        else:seen[key]=row['id']
    return pairs

def shortlist(workspace,course,rows,scope,kind=None,limit=12,used_ids=()):
    from homework import allowed,topic_matches
    if type(limit) is not int or not 1<=limit<=32:raise ValueError('Shortlist limit must be 1-32; retrieval does not download images')
    papers=allowed(course,scope['level']);topics=scope.get('topics',[]);exclude=set(used_ids)|set(scope.get('exclude_ids',[]));seen=set(scope.get('seen_candidate_ids',[]))
    candidates=[r for r in rows if r['paper'] in papers and r['id'] not in (exclude|seen) and (not kind or r['kind']==kind) and (not topics or any(topic_matches(t,label) for t in topics for label in r.get('topics',[])+r.get('subtopics',[])))]
    query=scope.get('query','');terms=tokens(query);rank={};db=ensure_fts(workspace,course,rows)
    if terms:
        expression=' OR '.join('"'+t.replace('"','""')+'"' for t in terms)
        matched=db.execute('select id,bm25(question_fts,0,2,1) as relevance from question_fts where question_fts match ? order by relevance',(expression,)).fetchall()
        rank={ident:i for i,(ident,_) in enumerate(matched)}
    db.close();texts=corpus();scored=[]
    for r in candidates:
        if terms and r['id'] not in rank:continue
        text=row_text(r,texts);lower=text.lower()
        hits=[x for x in scope.get('exclude_terms',[]) if str(x).lower() in lower]
        if scope.get('whole_questions_only') and hits:continue
        score=(20/(1+rank[r['id']]) if terms else 0)+2*sum(t in lower for t in terms)+(.02*(r.get('year',2000)-2000))+2*(r.get('difficulty')==scope.get('difficulty','medium'))-3*len(hits)-max(0,len(r.get('topics',[]))-1)
        scored.append((score,r,text,hits))
    # Reviewed portable excerpts participate in the same retrieval, for every topic.
    from excerpts import all_recipes
    recipe_data=all_recipes(workspace,course)
    by_id={r['id']:r for r in rows}
    for rec in recipe_data:
        parent=by_id.get(rec['original_id'])
        if rec['course']!=course or not parent or parent['paper'] not in papers or rec['original_id'] in exclude or rec['id'] in (exclude|seen) or (kind and kind!='structured') or scope.get('whole_questions_only'):continue
        if topics and not any(topic_matches(t,label) for t in topics for label in rec['topics']+rec['subtopics']):continue
        text=rec['retrieval_text'];lower=text.lower();n=sum(t in lower for t in terms)
        if terms and not n:continue
        hits=[x for x in scope.get('exclude_terms',[]) if str(x).lower() in lower]
        row={**parent,**rec,'kind':'structured','corrected_marks':rec['marks'],'portable_recipe':True}
        scored.append((6+2*n-3*len(hits),row,text,hits))
    scored.sort(key=lambda x:(-x[0],x[1]['id']));seen=set();seen_ids=set();result=[]
    for score,r,text,hits in scored:
        fp=fingerprint(text,r)
        if fp in seen or r['id'] in seen_ids:continue
        seen.add(fp);seen_ids.add(r['id'])
        result.append({'id':r['id'],'kind':r['kind'],'marks':r['marks'],'difficulty':r['difficulty'],'source_ref':r['source_ref'],'topics':r['topics'],'subtopics':r['subtopics'],'snippet':text[:1200],'possible_cross_scope_terms':hits,'portable_recipe':r.get('portable_recipe',False),'requires_lesson_and_answer_review':True})
        if len(result)>=limit:break
    return {'candidates':result,'matched_metadata_count':len(scored),'media_downloaded':0,'note':'Text/tags shortlist only. Review retained question, answer, prerequisites and taught-example duplication.'}

def coverage(rows_by_course):
    result=[]
    for course,rows in rows_by_course.items():
        for topic in sorted({t for r in rows for t in r['topics'] if t.startswith('Topic ') or (course=='0625' and re.match(r'^[1-6] ',t))},key=lambda t:int(code(t))):
            members=[r for r in rows if topic in r['topics']]
            result.append({'course':course,'topic':topic,'question_count':len(members),'mcq':sum(r['kind']=='mcq' for r in members),'structured':sum(r['kind']=='structured' for r in members),'semantic_all_items_reviewed':False})
    return result
