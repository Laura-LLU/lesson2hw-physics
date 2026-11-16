"""Mechanical protocol tests using synthetic assets, never real Agent acceptance."""
import unittest,tempfile,json,sys,subprocess,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
SCRIPTS=Path(__file__).resolve().parents[1]/'skill/lesson2hw-physics/scripts'

class FastProtocolIntegration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.work=self.root/'workspace'
        course=self.work/'9702';course.mkdir(parents=True)
        rows=[]
        for number in [1,2]:
            images={}
            for side in ['question','answer']:
                p=self.root/(str(number)+side+'.png');im=Image.new('RGB',(800,400),'white');d=ImageDraw.Draw(im);d.text((40,40),'Synthetic protocol fixture '+str(number)+' '+side,fill='black');d.text((40,110),'Constant speed means distance divided by time.',fill='black');im.save(p);images[side+'_image']=str(p)
            rows.append({'id':'fixture'+str(number),'course':'9702','paper':'1','kind':'mcq','marks':1,'topics':['Topic 2 · Kinematics'],'subtopics':[],'difficulty':'medium','source_ref':'synthetic mechanical fixture','search_text':'Constant speed distance divided by time '+str(number)+' '+('Second item unique description' if number==2 else 'First item distinct explanation'),**images})
        (course/'bank.json').write_text(json.dumps({'course':'9702','questions':rows}));self.rows=rows
        material=self.root/'lesson.png';Image.new('RGB',(800,400),'white').save(material)
        begin=self.call('begin','--material',str(material),'--request','one MCQ');self.job=begin['job'];self.sha=begin['input_sha256']
        scope={'course':'9702','level':'AS','topics':['2'],'query':'constant speed','include':['constant speed'],'exclude':[],'input_sha256':self.sha,'input_visually_reviewed':True,'requirements':{'counts':{'mcq':1}}}
        p=self.root/'scope.json';p.write_text(json.dumps(scope));prepared=self.call('prepare','--job',self.job,'--scope-file',str(p));self.assertTrue(prepared['layout_review_needed'])
        self.assessment=self.root/'assessment.json';self.assessment.write_text(json.dumps({'input_sha256':self.sha,'questions':{'fixture1':{'scope_pass':True,'answer_checked':True,'already_taught':False,'reason':'Synthetic fixture only, not semantic acceptance','question_layout':{},'answer_layout':{}}}}))
    def tearDown(self):self.temp.cleanup()
    def call(self,*args,ok=True):
        cp=subprocess.run([sys.executable,'-B',str(SCRIPTS/'fast.py'),'--workspace',str(self.work),*args],capture_output=True,text=True)
        if not ok:
            self.assertNotEqual(cp.returncode,0);return cp.stderr
        self.assertEqual(cp.returncode,0,cp.stderr);return json.loads(cp.stdout)
    def compose(self,title='Protocol fixture',ok=True):return self.call('compose','--job',self.job,'--assessment-file',str(self.assessment),'--title',title,ok=ok)
    def test_repeated_compose_is_idempotent_and_revisions_preserve_old_pdf(self):
        first=self.compose();before=Path(first['outputs']['student']).read_bytes();second=self.compose();self.assertTrue(second['idempotent_replay']);self.assertEqual(first['outputs'],second['outputs'])
        changed=self.compose('Revised title');self.assertNotEqual(first['outputs'],changed['outputs']);self.assertEqual(Path(first['outputs']['student']).read_bytes(),before)
    def test_unknown_geometry_is_blocked_before_export(self):
        assessment=json.loads(self.assessment.read_text());assessment['questions']['fixture1'].pop('answer_layout');self.assessment.write_text(json.dumps(assessment));self.assertIn('Unreviewed source geometry',self.compose(ok=False))
    def test_changed_asset_cannot_reuse_successful_compose(self):
        self.compose();Image.new('RGB',(800,400),'red').save(self.rows[0]['question_image']);self.assertIn('Asset changed after preview',self.compose(ok=False))
    def test_changed_pdf_after_render_cannot_be_finished(self):
        first=self.compose();p=Path(first['outputs']['student']);p.write_bytes(p.read_bytes()+b'changed')
        error=self.call('finish','--job',self.job,'--visual-reviewed','--delivery-note','synthetic test',ok=False);self.assertIn('Outputs changed after QA',error)
