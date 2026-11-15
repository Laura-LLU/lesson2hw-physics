import sys,tempfile,unittest
from pathlib import Path
from PIL import Image,ImageDraw
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skill/lesson2hw-physics/scripts'))
import pdf_engine as engine

class WebsitePdfStyle(unittest.TestCase):
    def make_pdf(self,root,size=(1000,3600),answer=False,title='Physics worksheet'):
        image=Image.new('RGB',size,'white');draw=ImageDraw.Draw(image)
        for y in range(15,size[1],100):draw.rectangle((15,y,size[0]-15,y+10),fill='black')
        source=root/'item.png';image.save(source)
        row={'id':'sample','kind':'structured','corrected_marks':7,'source_ref':'9702/43/O/N/21 Q1','question_image':str(source),'answer_image':str(source)}
        engine.BANK_ROOT=root;engine.CURRENT_COURSE='9702'
        output=root/'paper.pdf'
        engine.build_pdf([row],output,title,{'className':'Physics','dueDate':'2026-11-15','timeLimit':'30','totalMarks':7},answer)
        return PdfReader(output)
    def test_brand_and_current_total_page_numbers_on_every_page(self):
        with tempfile.TemporaryDirectory() as folder:
            pdf=self.make_pdf(Path(folder))
            self.assertGreater(len(pdf.pages),1)
            for n,page in enumerate(pdf.pages,1):
                text=page.extract_text()
                self.assertIn('Laura-LLU | github.com/Laura-LLU',text)
                self.assertIn(f'{n}/{len(pdf.pages)}',text)
                self.assertIn('9702 Physics',text)
                self.assertNotIn('Lesson2HW',text)
                self.assertAlmostEqual(float(page.mediabox.width),595.28,places=2)
            self.assertIn('STUDENT PAPER',pdf.pages[0].extract_text())
            self.assertIn('Class: Physics',pdf.pages[0].extract_text())
            self.assertIn('9702 Physics | Student Paper',pdf.pages[1].extract_text())
    def test_first_page_never_contains_only_the_header(self):
        with tempfile.TemporaryDirectory() as folder:
            # 690pt image is larger than first-page room but fits a fresh continuation page.
            pdf=self.make_pdf(Path(folder),size=(1000,1329))
            self.assertIn('2021 Oct/Nov | Paper 43 | Q1 | 7 marks',pdf.pages[0].extract_text())
            self.assertTrue(pdf.pages[0].images)
    def test_answer_title_and_unicode_title_work(self):
        with tempfile.TemporaryDirectory() as folder:
            pdf=self.make_pdf(Path(folder),size=(1000,500),answer=True,title='圆周运动 作业')
            text=pdf.pages[0].extract_text()
            self.assertIn('MARK SCHEME',text)
            self.assertIn('1/1',text)
            self.assertEqual(pdf.metadata.author,'Laura-LLU')

if __name__=='__main__':unittest.main()
