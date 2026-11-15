import unittest,tempfile,json,sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'skill/lesson2hw-physics/scripts'
sys.path.insert(0,str(SCRIPTS))
from homework import allowed,normalize,load_bank

class IGCSEPaperPolicy(unittest.TestCase):
    def test_allowed_components_are_exactly_246(self):
        self.assertEqual(allowed('0625','Extended')|allowed('0625','P6'),{'2','4','6'})
        for level in ['Core','P5']:
            with self.assertRaises(ValueError):allowed('0625',level)
        self.assertEqual(allowed('9702','P3'),{'3'})
        self.assertEqual(allowed('9702','P5'),{'5'})
    def test_custom_import_rejects_other_components(self):
        for paper in ['1','3','5','Paper 11','Paper 31','Paper 51']:
            with self.assertRaisesRegex(ValueError,'只允许Paper'):
                normalize('0625',{'course':'0625','paper':paper},ROOT)
    def test_authorized_p6_material_can_be_imported(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)
            Image.new('RGB',(20,20),'white').save(source/'paper.png')
            row={'id':'my-p6','course':'0625','paper':'Paper 61','kind':'structured',
                 'topics':['1 Motion, forces and energy'],'difficulty':'easy','marks':2,
                 'question_image':'paper.png','answer_image':'paper.png'}
            self.assertEqual(normalize('0625',row,source)['paper'],'6')
    def test_old_bank_excludes_other_papers_without_overwriting(self):
        with tempfile.TemporaryDirectory() as folder:
            work=Path(folder);target=work/'0625/bank.json';target.parent.mkdir()
            raw=json.dumps({'course':'0625','questions':[{'id':str(p),'paper':str(p)} for p in range(1,7)]})
            target.write_text(raw)
            self.assertEqual({r['paper'] for r in load_bank(work,'0625')},{'2','4','6'})
            self.assertEqual(target.read_text(),raw)
    def test_missing_p6_is_reported_explicitly(self):
        with tempfile.TemporaryDirectory() as folder:
            cp=subprocess.run([sys.executable,'-B',str(SCRIPTS/'homework.py'),'--workspace',folder,'search','--course','0625','--level','P6'],text=True,capture_output=True)
            self.assertEqual(cp.returncode,0,cp.stderr)
            result=json.loads(cp.stdout)
            self.assertEqual(result['matches'],0)
            self.assertIn('没有0625 Paper 6素材',result['note'])

if __name__=='__main__':unittest.main()
