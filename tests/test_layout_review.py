import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from PIL import Image,ImageDraw
import pdfplumber
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skill/lesson2hw-physics/scripts'))
from material_layout import prepare_material,white_runs
from worksheet_plan import validate_review,choose_plan,validate_reviewed_assets
import pdf_engine as engine
from homework import normalize
from builtin_bank import ensure_assets

class LayoutReview(unittest.TestCase):
    def test_masks_are_hash_bound_and_sources_stay_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'source.png';im=Image.new('RGB',(400,300),'white');d=ImageDraw.Draw(im)
            d.rectangle((2,5,10,20),fill='black');d.rectangle((50,40,390,260),outline=(249,249,249));im.save(p)
            digest=hashlib.sha256(p.read_bytes()).hexdigest()
            prepared,audit=prepare_material(p,{'question_layout':{'sha256':digest,'masks':[[0,0,.04,.1]]}})
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),digest)
            self.assertEqual(prepared.convert('L').histogram()[249],im.convert('L').histogram()[249])
            self.assertEqual(prepared.convert('L').histogram()[0],0)
            self.assertTrue(audit['reviewed_geometry'])
            with self.assertRaisesRegex(ValueError,'stale'):
                prepare_material(p,{'question_layout':{'sha256':'0'*64}})

    def test_faint_full_width_stroke_is_not_a_white_band(self):
        im=Image.new('RGB',(100,100),'white');ImageDraw.Draw(im).line((0,50,99,50),fill=(249,249,249))
        self.assertFalse(any(t<=50<b for t,b in white_runs(im)))

    def test_protected_figure_and_caption_remain_in_one_pdf_slice(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);p=root/'source.png';im=Image.new('RGB',(1000,2600),'white');d=ImageDraw.Draw(im)
            d.rectangle((50,10,900,180),fill='black')
            d.rectangle((100,600,850,1400),outline='black',width=3)
            d.text((300,1470),'Figure 1.1',fill='black')
            d.rectangle((50,1700,900,2580),outline='black',width=3);im.save(p)
            row={'id':'test','kind':'structured','corrected_marks':5,'source_ref':'9702/42/M/J/26 Q1','question_image':str(p),'answer_image':str(p),'question_layout':{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'keep_together':[[0,.22,1,.59]]}}
            engine.BANK_ROOT=root;engine.CURRENT_COURSE='9702';dest=root/'student.pdf'
            audit=engine.build_pdf([row],dest,'Protected figure',{'totalMarks':5},False)
            protected=audit[0]['protected_ranges'];offset=0
            with pdfplumber.open(dest) as pdf:
                self.assertGreater(len(pdf.pages),1)
                for page in pdf.pages:
                    self.assertTrue(page.images,'Every page has body content')
                    for image in sorted(page.images,key=lambda x:x['top']):
                        offset+=image['srcsize'][1]
                        self.assertFalse(any(t<offset<b for t,b in protected),'Figure or caption was split')

    def test_review_cannot_silently_switch_to_different_images(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'q.png';Image.new('RGB',(20,20),'white').save(p)
            rows=[{'id':'q','question_image':str(p),'answer_image':str(p)}]
            sha=hashlib.sha256(p.read_bytes()).hexdigest();review={'questions':{'q':{'question_sha256':sha,'answer_sha256':sha}}}
            validate_reviewed_assets(rows,review)
            Image.new('RGB',(20,20),'black').save(p)
            with self.assertRaisesRegex(ValueError,'changed'):validate_reviewed_assets(rows,review)

    def test_imported_excerpt_uses_retained_marks(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);Image.new('RGB',(20,20),'white').save(root/'q.png')
            row={'id':'part','paper':'4','kind':'structured','topics':['1.2'],'difficulty':'medium','marks':3,'corrected_marks':10,'question_image':'q.png','answer_image':'q.png','excerpt':True}
            row.update({'source_kind':'builtin','question_asset':'old','answer_asset':'old'})
            imported=normalize('0625',row,root)
            self.assertEqual(imported['corrected_marks'],3)
            self.assertNotIn('source_kind',imported)
            self.assertNotIn('question_asset',imported)
            before=(root/'q.png').read_bytes();ensure_assets([imported]);self.assertEqual((root/'q.png').read_bytes(),before)
            with self.assertRaisesRegex(ValueError,'independent local material'):ensure_assets([row])

class RequirementsReview(unittest.TestCase):
    def rows(self):return [{'id':str(i),'kind':'structured','marks':10} for i in range(3)]
    def review(self,rows):
        return {'course':'9702','level':'A2','scope':{'include':'circular motion','exclude':['gravity']},'requirements':{'counts':{'structured':3}},'questions':{r['id']:{'scope_pass':True,'answer_checked':True,'already_taught':False,'independently_answerable':True,'reason':'Inspected all retained circular-motion parts'} for r in rows}}
    def test_wrong_quantity_fails(self):
        rows=self.rows();self.assertFalse(validate_review('9702','A2',rows[:2],self.review(rows))['passed'])
    def test_excerpts_cannot_satisfy_complete_questions(self):
        rows=self.rows();rows[0]['excerpt']=True;r=self.review(rows);r['requirements']['whole_questions_only']=True
        self.assertFalse(validate_review('9702','A2',rows,r)['passed'])
    def test_independent_excerpt_groups_are_allowed(self):
        rows=self.rows()
        for r in rows:r['excerpt']=True
        review=self.review(rows);review['requirements']['whole_questions_only']=False
        result=validate_review('9702','A2',rows,review)
        self.assertTrue(result['passed']);self.assertEqual(result['excerpt_groups'],3)
        self.assertEqual(result['complete_original_structured'],0)

    def test_excerpt_without_independence_review_is_rejected(self):
        rows=self.rows();rows[0]['excerpt']=True;review=self.review(rows)
        review['questions']['0']['independently_answerable']=False
        with self.assertRaisesRegex(ValueError,'independent-answerability'):validate_review('9702','A2',rows,review)

    def test_duration_is_calculated_from_material(self):
        rows=self.rows();r=self.review(rows);r['requirements']['minutes']=60
        self.assertEqual(validate_review('9702','A2',rows,r)['estimated_minutes'],45)
        self.assertFalse(validate_review('9702','A2',rows,r)['passed'])
    def test_unconfirmed_prerequisite_rejects_material(self):
        rows=self.rows();r=self.review(rows);r['questions']['0']['prerequisites']=[{'concept':'qV=KE','confirmed':False}]
        with self.assertRaisesRegex(ValueError,'Unconfirmed'):validate_review('9702','A2',rows,r)
    def test_planner_does_not_select_unreviewed_questions(self):
        rows=self.rows();r=self.review(rows);r['requirements']={'minutes':30,'counts':{'structured':2}}
        r['questions'].pop('2');chosen,check=choose_plan('9702','A2',rows,r)
        self.assertTrue(check['passed']);self.assertEqual([x['id'] for x in chosen],['0','1'])
    def test_unsafe_or_duplicate_question_is_rejected(self):
        rows=self.rows();r=self.review(rows);r['questions']['0']['already_taught']=True
        with self.assertRaisesRegex(ValueError,'scope/answer/duplicate'):validate_review('9702','A2',rows,r)

if __name__=='__main__':unittest.main()
