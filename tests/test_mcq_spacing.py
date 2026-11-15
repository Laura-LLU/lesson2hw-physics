import sys,tempfile,unittest
from pathlib import Path
from PIL import Image,ImageDraw
import pdfplumber
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skill/lesson2hw-physics/scripts'))
import pdf_engine as engine

class MCQSpacing(unittest.TestCase):
    def make_pdf(self,root,count,answer=False):
        source=root/'question.png';image=Image.new('RGB',(1000,150),'white')
        ImageDraw.Draw(image).rectangle((5,5,995,145),outline='black',width=2);image.save(source)
        rows=[{'id':str(i),'kind':'mcq','corrected_marks':1,'source_ref':f'0625/2/M/J/26 v1 Q{i}',
               'question_image':str(source),'answer_image':str(source)} for i in range(1,count+1)]
        engine.BANK_ROOT=root;engine.CURRENT_COURSE='0625'
        target=root/('answers.pdf' if answer else 'student.pdf')
        engine.build_pdf(rows,target,'Spacing test',{'totalMarks':count},answer)
        return target
    def labels(self,page):
        return [w for w in page.extract_words() if w['text'].endswith('.') and w['text'][:-1].isdigit()]
    def test_student_spacing_is_36pt_and_answers_stay_compact(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for answer,gap in [(False,36),(True,14)]:
                with pdfplumber.open(self.make_pdf(root,2,answer)) as pdf:
                    labels=self.labels(pdf.pages[0]);self.assertEqual(len(labels),2)
                    image_height=150*(595.28-76)/1000
                    self.assertAlmostEqual(labels[1]['top']-labels[0]['top'],22+image_height+gap,places=2)
    def test_new_pages_do_not_inherit_extra_top_spacing(self):
        with tempfile.TemporaryDirectory() as folder:
            with pdfplumber.open(self.make_pdf(Path(folder),8)) as pdf:
                self.assertGreater(len(pdf.pages),1)
                self.assertEqual(sum(len(self.labels(p)) for p in pdf.pages),8)
                # The first question on a continuation page starts at the regular content origin.
                first=self.labels(pdf.pages[1])[0]
                self.assertLess(first['top'],75)
                self.assertIn(f'2/{len(pdf.pages)}',pdf.pages[1].extract_text())

if __name__=='__main__':unittest.main()
