from __future__ import annotations
from pathlib import Path
from urllib.parse import unquote
from io import BytesIO
from PIL import Image, ImageStat
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
BANK_ROOT = Path('.')
BRAND_NAME = 'LauraPhysics'
BRAND_URL = 'https://github.com/Laura-LLU'
BRAND_FOOTER = 'Laura-LLU | github.com/Laura-LLU'
CURRENT_COURSE = '9702'
PDF_FONT_NAME = 'PhysicsBankUnicode'
PDF_FONT_PATH = Path('/System/Library/Fonts/Supplemental/Arial Unicode.ttf')
if not PDF_FONT_PATH.is_file():
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    PDF_FONT_NAME = 'STSong-Light'
    pdfmetrics.registerFont(UnicodeCIDFont(PDF_FONT_NAME))
SESSION_CODES = {'Feb/Mar':'F/M','May/Jun':'M/J','Oct/Nov':'O/N'}


def as_int(value, default=0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def effective_marks(item: dict) -> int:
    corrected = as_int(item.get("corrected_marks"))
    if corrected:
        return corrected
    marks = as_int(item.get("marks_detected"))
    if marks:
        return marks
    if item.get("kind") == "mcq":
        return 1
    return 0

def source_ref(item: dict) -> str:
    return item.get("source_ref", item.get("id", ""))


def safe_under(root: Path, relative: str) -> Path:
    candidate = (root / unquote(relative)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError("文件路径超出允许范围。") from exc
    return candidate

def _best_cut(image: Image.Image, start: int, target: int) -> int:
    """Split only within continuous white bands; never choose a faint diagram row."""
    if target >= image.height:
        return image.height
    width = min(500, image.width)
    sample = image.convert("L").resize((width, max(1, round(image.height * width / image.width))))
    scale = image.height / sample.height
    minimum = int((start + max(80, (target-start)*0.20)) / scale)
    maximum = min(sample.height, int((target + (target-start)*0.04) / scale))
    px = sample.load()
    groups = []
    run = None
    for y in range(minimum, maximum):
        blank = all(px[x, y] >= 242 for x in range(2, width-2))
        if blank and run is None:
            run = y
        if not blank and run is not None:
            if y-run >= 4:
                groups.append((run,y))
            run = None
    if run is not None and maximum-run >= 4:
        groups.append((run,maximum))
    if not groups:
        # Preserve the whole remaining block and let page fitting scale it rather than cut a diagram.
        return image.height
    end = max(groups,key=lambda pair:pair[1])
    return min(image.height,max(start+1,int(((end[0]+end[1])/2)*scale)))


def _trim_outer_whitespace(image: Image.Image) -> Image.Image:
    """Trim the outer margin only; retain all separated text/diagram blocks."""
    gray = image.convert("L")
    ink = gray.point(lambda value: 255 if value < 246 else 0)
    box = ink.getbbox()
    if box is None:
        return image
    left, top, right, bottom = box
    return image.crop((max(0,left-8), max(0,top-8), min(image.width,right+8), min(image.height,bottom+8)))


def _crop_mcq_trailing_pages(image: Image.Image) -> Image.Image:
    """Remove page numbers, BLANK PAGE sheets, and copyright tails after Paper 1 Q40."""
    gray = image.convert("L")
    sample_width = min(500, gray.width)
    sample_height = max(1, int(gray.height * sample_width / gray.width))
    sample = gray.resize((sample_width, sample_height))
    threshold = max(3, int(sample_width * 0.006))
    active_rows = []
    for y in range(sample.height):
        row = sample.crop((0, y, sample.width, y + 1))
        if sum(pixel < 242 for pixel in row.getdata()) >= threshold:
            active_rows.append(y)
    groups: list[list[int]] = []
    join_gap = max(4, int(sample_width * 0.018))
    for y in active_rows:
        if not groups or y > groups[-1][-1] + join_gap:
            groups.append([y])
        else:
            groups[-1].append(y)
    accumulated_height = 0
    large_gap = max(180, int(sample_width * 0.42))
    for current, following in zip(groups, groups[1:]):
        accumulated_height += current[-1] - current[0] + 1
        if accumulated_height >= 12 and following[0] - current[-1] >= large_gap:
            scale = image.height / sample.height
            cutoff = min(image.height, int((current[-1] + 1) * scale) + 34)
            if cutoff < image.height * 0.82:
                return image.crop((0, 0, image.width, cutoff))
            break
    return image

def _compress_excess_vertical_whitespace(image: Image.Image) -> Image.Image:
    """Keep useful writing space while shortening oversized blank gaps in structured questions."""
    gray = image.convert("L")
    threshold = max(3, int(image.width * 0.006))
    active_rows = []
    for y in range(gray.height):
        row = gray.crop((0, y, gray.width, y + 1))
        if sum(pixel < 242 for pixel in row.getdata()) >= threshold:
            active_rows.append(y)
    if not active_rows:
        return image
    groups: list[list[int]] = []
    join_gap = max(5, int(image.width * 0.012))
    for y in active_rows:
        if not groups or y > groups[-1][-1] + join_gap:
            groups.append([y])
        else:
            groups[-1].append(y)
    max_gap = max(150, int(image.width * 0.22))
    kept_gap = max(96, int(image.width * 0.135))
    pieces: list[Image.Image] = []
    cursor = 0
    for current, following in zip(groups, groups[1:]):
        gap_start = current[-1] + 1
        gap_end = following[0]
        if gap_end - gap_start > max_gap:
            pieces.append(image.crop((0, cursor, image.width, gap_start)))
            pieces.append(Image.new("RGB", (image.width, kept_gap), "white"))
            cursor = gap_end
    pieces.append(image.crop((0, cursor, image.width, image.height)))
    if len(pieces) == 1:
        return image
    compacted = Image.new("RGB", (image.width, sum(piece.height for piece in pieces)), "white")
    y = 0
    for piece in pieces:
        compacted.paste(piece, (0, y))
        y += piece.height
    return compacted

def prepare_question_image(path: Path, item: dict) -> Image.Image:
    with Image.open(path) as opened:
        image = opened.convert("RGB")
    if item.get("kind") == "mcq" and as_int(item.get("question")) == 40:
        image = _crop_mcq_trailing_pages(image)
    elif item.get("kind") != "mcq":
        image = _compress_excess_vertical_whitespace(image)
    return _trim_outer_whitespace(image)

def _strip_trailing_table_header(image: Image.Image) -> Image.Image:
    """Drop an empty next-page mark-scheme table header left at the crop tail."""
    gray = image.convert("L")
    strong_rows = []
    for y in range(gray.height):
        row = list(gray.crop((0, y, gray.width, y + 1)).getdata())
        if sum(pixel < 130 for pixel in row) / gray.width > 0.60:
            strong_rows.append(y)
    if not strong_rows:
        return image
    groups: list[list[int]] = []
    for y in strong_rows:
        if not groups or y > groups[-1][-1] + 2:
            groups.append([y])
        else:
            groups[-1].append(y)
    last_line = groups[-1][0]
    tail_height = image.height - last_line
    if tail_height <= max(90, int(image.height * 0.14)):
        tail = gray.crop((0, min(image.height, last_line + 2), gray.width, image.height))
        if tail.height:
            preview_width = min(400, tail.width)
            preview_height = max(1, int(tail.height * preview_width / tail.width))
            preview = tail.resize((preview_width, preview_height))
            ink_ratio = sum(pixel < 225 for pixel in preview.getdata()) / (preview.width * preview.height)
            if ink_ratio > 0.012:
                return image.crop((0, 0, image.width, max(1, last_line - 6)))
    return image

def split_image(path: Path, width_points: float, max_height_points: float, item: dict, answer: bool) -> list[Image.Image]:
    if answer:
        with Image.open(path) as opened:
            image = _trim_outer_whitespace(_strip_trailing_table_header(opened.convert("RGB")))
    else:
        image = prepare_question_image(path, item)
    scaled_height = image.height * width_points / image.width
    if scaled_height <= max_height_points:
        return [image]
    max_pixels = max(300, int(max_height_points * image.width / width_points))
    slices: list[Image.Image] = []
    start = 0
    while start < image.height:
        target = min(image.height, start + max_pixels)
        end = _best_cut(image, start, target) if target < image.height else image.height
        if end <= start:
            end = target
        if image.height - end <= max_pixels * 0.13:
            end = image.height
        part = image.crop((0, start, image.width, end))
        preview_height = max(1, int(part.height * 300 / part.width))
        preview = part.convert("L").resize((300, preview_height))
        ink_ratio = sum(1 for pixel in preview.getdata() if pixel < 238) / (preview.width * preview.height)
        if ink_ratio >= 0.0018:
            slices.append(part)
        start = end
    return slices or [image]

class NumberedCanvas(canvas.Canvas):
    """Defer page finalization so every footer can contain current/total pages."""
    def __init__(self, *args, footer, **kwargs):
        super().__init__(*args, **kwargs)
        self._page_states = []
        self._footer_callback = footer

    def showPage(self):
        self._page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._page_states)
        for state in self._page_states:
            self.__dict__.update(state)
            self._footer_callback(self, self._pageNumber, total)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)


def _row_profile(image):
    import math
    scan_width = min(900, image.width)
    factor = scan_width / image.width
    sample = image.resize((scan_width, max(1, math.floor(image.height * factor + .5)))).convert('RGB')
    pixels = sample.load()
    left, right = int(scan_width * .025), math.ceil(scan_width * .975)
    scores, spans = [], []
    for y in range(sample.height):
        dark = [x for x in range(left, right, 2) if sum(pixels[x,y]) < 720]
        scores.append(len(dark))
        spans.append(dark[-1] - dark[0] + 1 if dark else 0)
    return {'scores':scores,'spans':spans,'width':scan_width,'factor':factor,
            'blank':max(2,int(((right-left)/2)*.006))}


def _web_slice_height(image, profile, offset, maximum):
    """Match the public site's blank-band pagination and short-tail handling."""
    import math
    remaining = image.height - offset
    if remaining <= maximum:return remaining
    scores, spans, factor = profile['scores'], profile['spans'], profile['factor']
    minimum = min(maximum,max(120,int(maximum*.55)))
    start = max(0,math.ceil((offset+minimum)*factor))
    end = min(len(scores)-1,math.floor((offset+maximum-4)*factor))
    run_min = max(8,math.floor(36*factor+.5))
    def substantial(cut,stop):
        row = cut+1
        while row<=stop and scores[row]<=profile['blank']:row+=1
        ink=span=blank=0
        while row<=stop:
            if scores[row]<=profile['blank']:
                blank+=1
                if blank>=run_min:break
            else:
                blank=0;ink+=scores[row];span=max(span,spans[row])
            row+=1
        return span>=profile['width']*.16 or ink>=profile['width']*.28
    run_end=-1
    for row in range(end,start-1,-1):
        if scores[row]<=profile['blank']:
            if run_end<0:run_end=row
        else:
            if run_end>=0 and run_end-row>=run_min:
                cut=(row+1+run_end)//2
                stop=min(len(scores)-1,cut+max(100,math.floor(260*factor+.5)))
                if substantial(cut,stop):return max(1,math.floor(cut/factor)-offset)
            run_end=-1
    if run_end>=0 and run_end-start+1>=run_min:
        return max(1,math.floor(((start+run_end)//2)/factor)-offset)
    # As on the website, prefer the least-ink row if no usable blank band exists.
    best, best_score = end, float('inf')
    for row in range(max(start,math.floor(end-(end-start)*.35)),end+1):
        values=[scores[i] for i in range(row-2,row+3) if 0<=i<len(scores)]
        score=sum(values)/len(values)
        if score<=best_score:best,best_score=row,score
    return max(1,math.floor(best/factor)-offset)


def _web_item_meta(number,item):
    import re
    match = re.match(r'^(?:9702|0625)/(\d+)/(F/M|M/J|O/N)/(\d{2})(?:\s+v\d+)?\s+Q(\d+)',source_ref(item))
    marks = effective_marks(item)
    mark_text = str(marks) if marks else '?'
    if match:
        paper,session,year,question=match.groups()
        session={'F/M':'Feb/Mar','M/J':'May/Jun','O/N':'Oct/Nov'}[session]
        return f'{number}. 20{year} {session} | Paper {paper} | Q{int(question)} | {mark_text} marks'
    return f'{number}. {source_ref(item)} | {mark_text} marks'


class PdfComposer:
    """LauraPhysics.com layout: inset first-page card, compact continuation, N/total footer."""
    def __init__(self, output: Path, title: str, metadata: dict, answer: bool):
        output.parent.mkdir(parents=True,exist_ok=True)
        self.page_width,self.page_height=595.28,841.89
        self.margin=38
        self.content_width=self.page_width-2*self.margin
        self.title,self.metadata,self.answer=title,metadata,answer
        self.course=CURRENT_COURSE
        self.page_no=0
        self.y=0
        self.pdf=NumberedCanvas(str(output),pagesize=(self.page_width,self.page_height),footer=self._footer)
        self.pdf.setTitle(title)
        self.pdf.setAuthor('Laura-LLU')
        self.pdf.setSubject(f'{self.course} Physics | '+('Mark Scheme' if answer else 'Student Paper'))
        try:pdfmetrics.getFont(PDF_FONT_NAME)
        except KeyError:
            if not PDF_FONT_PATH.is_file():raise RuntimeError(f'Missing PDF font: {PDF_FONT_PATH}')
            pdfmetrics.registerFont(TTFont(PDF_FONT_NAME,str(PDF_FONT_PATH)))

    def _text(self,text,x,y,size,font='Helvetica',color='#172336',max_width=None):
        if any(ord(c)>255 for c in text):font=PDF_FONT_NAME
        if max_width:
            while size>6 and pdfmetrics.stringWidth(text,font,size)>max_width:size-=.25
            if pdfmetrics.stringWidth(text,font,size)>max_width:
                while text and pdfmetrics.stringWidth(text+'...',font,size)>max_width:text=text[:-1]
                text+='...'
        self.pdf.setFillColor(HexColor(color));self.pdf.setFont(font,size)
        self.pdf.drawString(x,y,text)

    def new_page(self):
        if self.page_no:self.pdf.showPage()
        self.page_no+=1
        self.items_on_page=0
        top=self.page_height-self.margin
        if self.page_no==1:
            factor=self.content_width/1600
            height=310*factor
            self.pdf.setFillColor(HexColor('#132a46'))
            self.pdf.rect(self.margin,top-164*factor,self.content_width,164*factor,fill=1,stroke=0)
            self.pdf.setFillColor(HexColor('#d8493f'))
            self.pdf.rect(self.margin,top-174*factor,self.content_width,10*factor,fill=1,stroke=0)
            self._text(self.title,self.margin+52*factor,top-82*factor,54*factor,'Helvetica-Bold','#ffffff',1495*factor)
            self._text('MARK SCHEME' if self.answer else 'STUDENT PAPER',self.margin+52*factor,top-132*factor,28*factor,'Helvetica-Bold','#b9d5ef')
            fields=[('Class',self.metadata.get('className'),52,465),('Student',self.metadata.get('studentName'),540,500),('Date',self.metadata.get('dueDate'),1080,470)]
            for label,value,x,width in fields:
                self._text(f'{label}: {value or "____________"}',self.margin+x*factor,top-226*factor,30*factor,'Helvetica-Bold',max_width=width*factor)
            course_name='Cambridge IGCSE Physics 0625' if self.course=='0625' else 'Cambridge International AS & A Level Physics 9702'
            total=self.metadata.get('totalMarks',0)
            incomplete=self.metadata.get('marksIncomplete',0)
            marks=f'{total}' if not incomplete else f'{total} known ({incomplete} unknown)'
            line=f'{course_name}  |  Suggested time: {self.metadata.get("timeLimit") or "____"} minutes  |  Total marks: {marks}'
            self._text(line,self.margin+52*factor,top-280*factor,27*factor,'Helvetica','#526075',1495*factor)
            self.y=top-height-18
        else:
            self._text(f'{self.course} Physics | '+('Mark Scheme' if self.answer else 'Student Paper'),self.margin,top+2,9,'Helvetica-Bold','#596e8a')
            self.y=top-18

    def _footer(self,pdf,number,total):
        pdf.setStrokeColor(HexColor('#ccd4db'));pdf.setLineWidth(.5)
        pdf.line(self.margin,28,self.page_width-self.margin,28)
        pdf.setFillColor(HexColor('#d94a40'));pdf.circle(self.margin+7,16,7,fill=1,stroke=0)
        pdf.setFillColor(white);pdf.setFont('Helvetica-Bold',7);pdf.drawString(self.margin+4.5,13,'L')
        pdf.setFillColor(HexColor('#596e8a'));pdf.setFont('Helvetica-Bold',8)
        pdf.drawString(self.margin+20,13,'Laura-LLU | github.com/Laura-LLU')
        pdf.setFont('Helvetica',8);pdf.drawString(self.page_width-self.margin-118,13,f'{self.course} Physics')
        pdf.drawString(self.page_width-self.margin-24,13,f'{number}/{total}')

    def _continued(self,number):
        self.new_page()
        self._text(f'Question {number} continued',self.margin,self.y-12,8.5,'Helvetica','#596e8a')
        self.y-=20

    def add_item(self,number,item,image_path):
        import math
        if not self.page_no:self.new_page()
        with Image.open(image_path) as source:image=source.convert('RGB')
        scale=min(self.content_width/image.width,.75)
        if image.height*scale>1450:scale*=.98
        fresh=self.page_height-self.margin-18-38-22
        current=self.y-38-22
        if self.items_on_page and image.height*scale>current and (image.height*scale<=fresh or current<fresh*.72):self.new_page()
        self.pdf.setStrokeColor(HexColor('#ccd4db'));self.pdf.setLineWidth(.6)
        self.pdf.line(self.margin,self.y,self.page_width-self.margin,self.y)
        self._text(_web_item_meta(number,item),self.margin,self.y-14,9.5,'Helvetica-Bold',max_width=self.content_width)
        self.y-=22
        offset=0;profile=None
        while offset<image.height:
            available=self.y-38
            if available<70:self._continued(number);available=self.y-38
            maximum=max(1,math.floor(available/scale))
            remaining=image.height-offset
            merge=maximum<remaining<=maximum*1.08
            if remaining<=maximum or merge:height=remaining
            else:
                if profile is None:profile=_row_profile(image)
                height=_web_slice_height(image,profile,offset,maximum)
            slice_scale=available/height if merge else scale
            part=image.crop((0,offset,image.width,offset+height))
            buffer=BytesIO();part.save(buffer,format='PNG');buffer.seek(0)
            draw_height=height*slice_scale
            self.pdf.drawImage(ImageReader(buffer),self.margin,self.y-draw_height,image.width*slice_scale,draw_height,mask='auto')
            self.y-=draw_height+14;offset+=height;self.items_on_page+=1
            if offset<image.height:self._continued(number)

    def save(self):
        if not self.page_no:self.new_page()
        self.pdf.showPage();self.pdf.save()


def build_pdf(items: list[dict], output: Path, title: str, metadata: dict, answer: bool) -> None:
    composer=PdfComposer(output,title,metadata,answer)
    for number,item in enumerate(items,1):
        relative=item['answer_image'] if answer else item['question_image']
        composer.add_item(number,item,safe_under(BANK_ROOT,relative))
    composer.save()
