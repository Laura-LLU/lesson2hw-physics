"""Hash/page-bound lesson previews. No cloud model calls or inferred lesson scope."""
from pathlib import Path
import json,hashlib,zipfile,xml.etree.ElementTree as ET,subprocess,shutil
from PIL import Image

def parse_pages(value,total):
    if not value:return list(range(1,total+1))
    pages=[]
    for part in value.split(','):
        if '-' in part:
            first,last=map(int,part.split('-',1));pages+=list(range(first,last+1))
        else:pages.append(int(part))
    if not pages or min(pages)<1 or max(pages)>total:raise ValueError('Requested lesson pages outside source')
    return list(dict.fromkeys(pages))

def prepare(path,cache,pages=None,timeout_seconds=90):
    path=Path(path);digest=hashlib.sha256(path.read_bytes()).hexdigest()
    key=hashlib.sha256((digest+'|'+str(pages)+'|preview-v2').encode()).hexdigest()
    dest=Path(cache)/key;manifest=dest/'manifest.json'
    if manifest.exists():
        cached=json.loads(manifest.read_text())
        if all(Path(p).is_file() for p in cached.get('previews',[])):return {**cached,'cache_hit':True}
    dest.mkdir(parents=True,exist_ok=True);ext=path.suffix.lower();previews=[];texts=[]
    if ext in ['.txt','.md']:
        selected=[1];texts=[{'page':1,'text':path.read_text()}]
    elif ext in ['.png','.jpg','.jpeg','.webp']:
        image=Image.open(path).convert('RGB')
        # Tile long boards without discarding any part; leave fonts readable.
        factor=min(1,1500/image.width);image=image.resize((round(image.width*factor),round(image.height*factor)))
        for n,top in enumerate(range(0,image.height,1720),1):
            target=dest/f'board-{n:02d}.png';image.crop((0,max(0,top-80),image.width,min(image.height,top+1800))).save(target);previews.append(str(target))
        selected=[1]
    else:
        pdf=path
        if ext in ['.pptx','.ppt']:
            if ext=='.pptx':
                with zipfile.ZipFile(path) as z:
                    slides=[n for n in z.namelist() if __import__('re').fullmatch(r'ppt/slides/slide\d+\.xml',n)]
                    selected=parse_pages(pages,len(slides))
                    for pno in selected:
                        tree=ET.fromstring(z.read(f'ppt/slides/slide{pno}.xml'));texts.append({'page':pno,'text':' '.join(x.text or '' for x in tree.iter() if x.tag.endswith('}t'))})
            conversion=Path(cache)/('render-'+digest);conversion.mkdir(exist_ok=True);pdf=conversion/(path.stem+'.pdf')
            if not pdf.exists():
                exe=shutil.which('soffice') or '/Applications/LibreOffice.app/Contents/MacOS/soffice'
                if not Path(exe).is_file():raise RuntimeError('PPT rendering unavailable; use the host renderer for the exact requested pages, not guessed text-only scope')
                profile=Path(cache)/'office-profile'
                subprocess.run([exe,'-env:UserInstallation='+profile.resolve().as_uri(),'--headless','--convert-to','pdf','--outdir',str(conversion),str(path)],capture_output=True,text=True,check=True,timeout=max(1,min(90,timeout_seconds)))
        if not pdf.is_file() or pdf.suffix.lower()!='.pdf':raise ValueError('Unsupported lesson format')
        import pypdfium2 as pdfium
        doc=pdfium.PdfDocument(str(pdf));selected=parse_pages(pages,len(doc))
        for pno in selected:
            target=dest/f'page-{pno:03d}.jpg';doc[pno-1].render(scale=1.5).to_pil().convert('RGB').save(target,quality=92);previews.append(str(target))
    data={'input_sha256':digest,'requested_pages':pages,'rendered_pages':selected,'previews':previews,'text_hints':texts,'visual_review_required':True,'cache_hit':False}
    manifest.write_text(json.dumps(data,ensure_ascii=False,indent=2));return data
