import sys,tempfile,unittest,json,subprocess
from pathlib import Path
from PIL import Image
import pdfplumber
ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'skill/lesson2hw-physics/scripts'
sys.path.insert(0,str(SCRIPTS))
from homework import output_names,export_title

class ContentNames(unittest.TestCase):
    def test_teacher_topic_and_paired_names(self):
        title=export_title('  速度—时间图  ',[{'topics':['Motion']}])
        self.assertEqual(output_names('0625',title),('0625_速度—时间图_作业.pdf','0625_速度—时间图_答案.pdf'))
    def test_missing_title_uses_selected_scope(self):
        self.assertEqual(export_title(None,[{'topics':['Motion','Forces']},{'topics':['Motion']}]),'Motion与Forces')
        self.assertEqual(export_title(' ',[]),'物理综合练习')
    def test_names_stay_portable_and_inside_output(self):
        for title in ['../../速度/时间:*?图\n', '.', 'x'*300, 'CON', 'ab\u202ecd']:
            for name in output_names('0625',title):
                self.assertEqual(Path(name).name,name)
                self.assertLessEqual(len(name.encode('utf-8')),230)
                self.assertFalse(any(c in name for c in '<>:"/\\|?*\n'))
    def test_cli_returns_real_paths_and_protects_existing_output(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder);source=base/'source';source.mkdir();image=source/'q.png'
            Image.new('RGB',(1000,150),'white').save(image)
            workspace=base/'workspace';bank=workspace/'0625'/'bank.json';bank.parent.mkdir(parents=True)
            row={'id':'sample','course':'0625','paper':'2','kind':'mcq','topics':['Motion'],'marks':1,'corrected_marks':1,'source_ref':'0625 Paper 2 Q1','question_image':str(image),'answer_image':str(image)}
            bank.write_text(json.dumps({'course':'0625','questions':[row]}))
            args=[sys.executable,str(SCRIPTS/'homework.py'),'--workspace',str(workspace),'export','--course','0625','--level','Extended','--year','2026','--checked','--title','速度—时间图','sample']
            result=subprocess.run(args,capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stderr)
            paths=json.loads(result.stdout)
            for side,suffix in [('student','作业'),('answers','答案')]:
                p=Path(paths[side]);self.assertTrue(p.is_file());self.assertEqual(p.name,f'0625_速度—时间图_{suffix}.pdf')
                with pdfplumber.open(p) as pdf:self.assertIn('Laura-LLU',pdf.pages[0].extract_text())
            selection=json.loads(Path(paths['selection']).read_text());self.assertEqual(selection['title'],'速度—时间图')
            old=Path(paths['student']).read_bytes()
            repeat=subprocess.run(args+['--output-dir',str(Path(paths['student']).parent)],capture_output=True,text=True)
            self.assertNotEqual(repeat.returncode,0);self.assertIn('overwrite',repeat.stderr)
            self.assertEqual(Path(paths['student']).read_bytes(),old)
            again=subprocess.run(args,capture_output=True,text=True);self.assertEqual(again.returncode,0,again.stderr)
            self.assertNotEqual(json.loads(again.stdout)['student'],paths['student'])

if __name__=='__main__':unittest.main()
