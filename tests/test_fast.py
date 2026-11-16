import sys,unittest,tempfile,json,hashlib,time,subprocess,copy
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];SCRIPTS=ROOT/'skill/lesson2hw-physics/scripts';sys.path.insert(0,str(SCRIPTS))
from homework import load_bank
from retrieval import shortlist,coverage,corpus
from excerpts import materialize
from input_cache import prepare
from worksheet_plan import validate_review,choose_plan

class FastRetrieval(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.workspace=Path(cls.temp.name)
        cls.rows={c:load_bank(cls.workspace,c) for c in ['9702','0625']}
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_all_31_theory_topics_retrieve_without_media(self):
        matrix=coverage(self.rows);self.assertEqual(len(matrix),31)
        for entry in matrix:
            course=entry['course'];number=int(entry['topic'].split()[1] if course=='9702' else entry['topic'].split()[0]);level=('AS' if number<=11 else 'A2') if course=='9702' else 'Extended'
            scope={'level':level,'topics':[str(number)],'query':'','include':[entry['topic']],'exclude':[]}
            got=shortlist(self.workspace,course,self.rows[course],scope,limit=3)
            self.assertTrue(got['candidates'],entry);self.assertEqual(got['media_downloaded'],0)
        self.assertFalse((self.workspace/'builtin-assets').exists())
    def test_full_corpus_is_present_and_no_approval_is_invented(self):
        self.assertEqual(len(corpus()),6586)
        got=shortlist(self.workspace,'9702',self.rows['9702'],{'level':'AS','topics':['2'],'query':'horizontal projectile'},'structured',4)
        self.assertTrue(got['candidates']);self.assertTrue(all(r['requires_lesson_and_answer_review'] for r in got['candidates']))
    def test_large_queries_do_not_trigger_bulk_downloads(self):
        with self.assertRaisesRegex(ValueError,'1-32'):shortlist(self.workspace,'9702',self.rows['9702'],{'level':'AS'},limit=250)
        self.assertFalse((self.workspace/'builtin-assets').exists())
    def test_second_round_excludes_seen_exact_ids(self):
        scope={'level':'AS','topics':['2'],'query':'horizontal projectile'}
        first=shortlist(self.workspace,'9702',self.rows['9702'],scope,'mcq',4)['candidates'];seen=[r['id'] for r in first]
        second=shortlist(self.workspace,'9702',self.rows['9702'],{**scope,'seen_candidate_ids':seen},'mcq',4)['candidates']
        self.assertFalse(set(seen)&{r['id'] for r in second})
    def test_0625_does_not_use_p5_to_fill_p6(self):
        got=shortlist(self.workspace,'0625',self.rows['0625'],{'level':'P6','query':'experiment'},limit=3)
        self.assertEqual(got['candidates'],[])

class PortableRecipeAndInput(unittest.TestCase):
    def test_excerpt_reconstruction_is_hash_bound_and_read_only(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);q=root/'q.png';a=root/'a.png';im=Image.new('RGB',(100,100),'white');ImageDraw.Draw(im).rectangle((10,10,80,80),outline='black');im.save(q);im.save(a)
            digest=hashlib.sha256(q.read_bytes()).hexdigest();recipe={'id':'parent-part-a','original_id':'parent','course':'0625','marks':3,'source_ref':'0625/4/M/J/26 Q1(a)','question_source_sha256':digest,'answer_source_sha256':digest,'question_boxes':[[0,0,1,.5]],'answer_boxes':[[0,0,1,.5]]}
            parent={'id':'parent','kind':'structured','marks':10,'question_image':str(q),'answer_image':str(a)}
            row=materialize(root,recipe,parent);self.assertEqual(row['marks'],3);self.assertEqual(hashlib.sha256(q.read_bytes()).hexdigest(),digest)
            self.assertNotIn('source_kind',row);Image.new('RGB',(100,100),'black').save(q)
            with self.assertRaisesRegex(ValueError,'source changed'):materialize(root,recipe,parent)
    def test_input_cache_changes_with_content_and_preserves_requested_pages(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);p=root/'board.png';Image.new('RGB',(1000,4000),'white').save(p)
            first=prepare(p,root/'cache');second=prepare(p,root/'cache')
            self.assertFalse(first['cache_hit']);self.assertTrue(second['cache_hit']);self.assertEqual(len(first['previews']),3)
            Image.new('RGB',(1000,4000),'black').save(p);third=prepare(p,root/'cache');self.assertNotEqual(first['input_sha256'],third['input_sha256'])
    def test_section_duration_cannot_hide_behind_correct_total(self):
        rows=[{'id':'m','kind':'mcq','marks':1},{'id':'s','kind':'structured','marks':10}]
        review={'course':'9702','level':'AS','scope':{'include':['kinematics'],'exclude':[]},'requirements':{'minutes':19.5,'minutes_by_kind':{'mcq':10,'structured':9.5}},'questions':{r['id']:{'scope_pass':True,'answer_checked':True,'already_taught':False,'reason':'checked'} for r in rows}}
        check=validate_review('9702','AS',rows,review);self.assertFalse(check['passed']);self.assertEqual(check['estimated_minutes'],19.5)

class FastDeadline(unittest.TestCase):
    def test_late_case_cannot_be_marked_delivered(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'job.json';p.write_text(json.dumps({'schema':1,'received_at_epoch':time.time()-301,'began_at_monotonic':time.monotonic()-301,'budget_seconds':300,'events':[],'status':'awaiting_visual_review'}))
            cp=subprocess.run([sys.executable,'-B',str(SCRIPTS/'fast.py'),'finish','--job',str(p),'--visual-reviewed','--delivery-note','checked'],capture_output=True,text=True)
            self.assertNotEqual(cp.returncode,0);self.assertIn('deadline exceeded',cp.stderr);self.assertEqual(json.loads(p.read_text())['status'],'failed')

if __name__=='__main__':unittest.main()

class BatchedPlanning(unittest.TestCase):
    def test_section_targets_choose_correct_split(self):
        rows=[{'id':'m'+str(i),'kind':'mcq','marks':1} for i in range(15)]+[{'id':'s'+str(i),'kind':'structured','marks':n} for i,n in enumerate([10,7,4])]
        review={'course':'9702','level':'AS','scope':{'include':['motion'],'exclude':[]},'requirements':{'minutes':40,'minutes_by_kind':{'mcq':20,'structured':20},'mixed':True},'questions':{r['id']:{'scope_pass':True,'answer_checked':True,'already_taught':False,'reason':'actual review'} for r in rows}}
        chosen,check=choose_plan('9702','AS',rows,review)
        self.assertTrue(check['passed']);self.assertEqual(sum(r['kind']=='mcq' for r in chosen),13);self.assertEqual(check['section_estimated_minutes']['structured'],19.8)
    def test_section_targets_alone_are_not_ignored(self):
        rows=[{'id':'s','kind':'structured','marks':10}]
        review={'course':'9702','level':'A2','scope':{'include':['gravity'],'exclude':[]},'requirements':{'minutes_by_kind':{'structured':15}},'questions':{'s':{'scope_pass':True,'answer_checked':True,'already_taught':False,'reason':'actual review'}}}
        chosen,check=choose_plan('9702','A2',rows,review);self.assertTrue(check['passed']);self.assertEqual(len(chosen),1)
    def test_begin_prepares_actual_input_in_one_step(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);material=root/'board.png';Image.new('RGB',(300,600),'white').save(material)
            cp=subprocess.run([sys.executable,'-B',str(SCRIPTS/'fast.py'),'--workspace',str(root/'workspace'),'begin','--material',str(material),'--request','three questions'],capture_output=True,text=True)
            self.assertEqual(cp.returncode,0,cp.stderr);data=json.loads(cp.stdout);self.assertTrue(Path(data['inputs'][0]['previews'][0]).is_file());self.assertEqual(len(data['input_sha256']),1)
    def test_asset_drift_cannot_be_rebound_by_compose(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);q=root/'q.png';Image.new('RGB',(100,100),'black').save(q)
            job={'schema':1,'received_at_epoch':time.time(),'began_at_monotonic':time.monotonic(),'budget_seconds':300,'inputs':[{'sha256':'lesson'}],'scope':{'course':'9702','level':'AS'},'preview_assets':{'id':{'question_sha256':'old','answer_sha256':'old'}},'fetched_rows':{'id':{'question_image':str(q),'answer_image':str(q)}},'events':[]}
            p=root/'job.json';p.write_text(json.dumps(job));a=root/'assessment.json';a.write_text(json.dumps({'input_sha256':['lesson'],'questions':{'id':{}}}))
            cp=subprocess.run([sys.executable,'-B',str(SCRIPTS/'fast.py'),'compose','--job',str(p),'--assessment-file',str(a),'--title','motion'],capture_output=True,text=True)
            self.assertNotEqual(cp.returncode,0);self.assertIn('Asset changed after preview',cp.stderr)

class BodyDeduplication(unittest.TestCase):
    def test_cross_session_reprints_and_ocr_spacing_are_duplicates(self):
        from retrieval import fingerprint
        row={'topics':['Topic 2 · Kinematics'],'subtopics':['2D · Two-dimensional motion']}
        a='Topic 2 · Kinematics 2D · Two-dimensional motion 6 A stone has horizontal velocity vH. What is its speed? A 4 B 6 C 8 D 10'
        b='Topic 2 · Kinematics 2D · Two-dimensional motion 5 A s tone has horizontal velocity v H. What is its speed? A 4 B 6 C 8 D 10 5 [Turn over'
        self.assertEqual(fingerprint(a,row),fingerprint(b,row));self.assertNotEqual(fingerprint(a,row),fingerprint(a.replace('D 10','D 12'),row))
    def test_real_two_reprints_are_detected(self):
        from retrieval import duplicate_pairs
        with tempfile.TemporaryDirectory() as folder:
            rows=load_bank(Path(folder),'9702');ids={'9702_s17_11_q06','9702_m23_12_q05','9702_w22_13_q05','9702_w18_13_q06'}
            self.assertEqual(len(duplicate_pairs([r for r in rows if r['id'] in ids])),2)

class PreviewLegibility(unittest.TestCase):
    def test_tall_source_is_tiled_not_shrunk_to_an_unreadable_strip(self):
        from fast import make_pairs,pack_previews
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);q=root/'q.png';a=root/'a.png'
            im=Image.new('RGB',(800,5000),'white');d=ImageDraw.Draw(im)
            for y in range(20,5000,50):d.text((20,y),'Readable source line at '+str(y),fill='black')
            im.save(q);Image.new('RGB',(800,1000),'white').save(a);before=q.read_bytes()
            pairs=make_pairs([{'id':'tall','kind':'structured','marks':10,'source_ref':'synthetic','question_image':str(q),'answer_image':str(a)}],root/'previews')
            self.assertGreaterEqual(len(pairs[0]['pair_previews']),3)
            with Image.open(pairs[0]['pair_previews'][0]) as preview:self.assertEqual(preview.width,1630)
            self.assertEqual(q.read_bytes(),before)
            self.assertEqual(len(pack_previews(pairs,root/'previews')),len(pairs[0]['pair_previews']))
    def test_missing_preview_cache_is_rebuilt(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);p=root/'board.png';Image.new('RGB',(300,300),'white').save(p)
            first=prepare(p,root/'cache');Path(first['previews'][0]).unlink();rebuilt=prepare(p,root/'cache');self.assertFalse(rebuilt['cache_hit']);self.assertTrue(Path(rebuilt['previews'][0]).is_file())
    def test_operator_can_record_failure_after_deadline_without_resetting_time(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'job.json';started=time.time()-310;p.write_text(json.dumps({'schema':1,'received_at_epoch':started,'began_at_monotonic':time.monotonic()-310,'budget_seconds':300,'events':[],'status':'scope_reviewed'}))
            cp=subprocess.run([sys.executable,'-B',str(SCRIPTS/'fast.py'),'abort','--job',str(p),'--reason','Timed trial stopped without delivered PDFs'],capture_output=True,text=True)
            self.assertEqual(cp.returncode,0,cp.stderr);saved=json.loads(p.read_text());self.assertEqual(saved['received_at_epoch'],started);self.assertEqual(saved['status'],'failed');self.assertFalse(saved['under_five_minutes'])

class RelaxedTimingAndText(unittest.TestCase):
    def test_target_overrun_does_not_end_new_ten_minute_job(self):
        from fast import budget
        self.assertGreater(budget({'received_at_epoch':time.time()-310,'began_at_monotonic':time.monotonic()-310,'budget_seconds':600}),280)
    def test_teacher_text_without_attachment_can_begin(self):
        with tempfile.TemporaryDirectory() as folder:
            cp=subprocess.run([sys.executable,'-B',str(SCRIPTS/'fast.py'),'--workspace',folder,'begin','--request','9702 AS motion, six MCQs'],capture_output=True,text=True)
            self.assertEqual(cp.returncode,0,cp.stderr);data=json.loads(cp.stdout);job=json.loads(Path(data['job']).read_text());self.assertEqual(job['budget_seconds'],600);self.assertEqual(job['target_seconds'],300);self.assertIn('six MCQs',data['inputs'][0]['text_hints'][0]['text'])
