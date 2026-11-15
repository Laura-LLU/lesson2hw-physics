"""Portable, non-destructive layout preparation. Geometry is reviewed by the host Agent.

Only identified source furniture is masked. White-space compaction removes fully
white rows, never faint diagram strokes. Original cached assets are read-only.
"""
from pathlib import Path
from functools import lru_cache
import hashlib,json,math
from PIL import Image,ImageDraw

@lru_cache(maxsize=1)
def guides():
    path=Path(__file__).resolve().parents[1]/'resources/layout-guides.json'
    return json.loads(path.read_text()).get('assets',{}) if path.is_file() else {}

def rectangle(value,width,height):
    if len(value)!=4 or any(type(x) not in (int,float) or not math.isfinite(x) for x in value):raise ValueError('Invalid layout rectangle')
    l,t,r,b=value
    if not (0<=l<r<=1 and 0<=t<b<=1):raise ValueError('Layout rectangle must be inside image')
    return round(l*width),round(t*height),round(r*width),round(b*height)

def white_runs(image):
    """Full-width strict white bands: preserves thin/faint graph and table edges."""
    gray=image.convert('L');runs=[];start=None
    for y in range(gray.height):
        blank=gray.crop((0,y,gray.width,y+1)).getextrema()[0]>=250
        if blank and start is None:start=y
        if not blank and start is not None:runs.append((start,y));start=None
    if start is not None:runs.append((start,gray.height))
    return runs

def compact_white(image,answer=False):
    threshold=max(80,round(image.width*.15))
    kept=max(36,round(image.width*(.035 if answer else .07)))
    pieces=[];cursor=0;removed=[]
    for top,bottom in white_runs(image):
        if top==0 or bottom==image.height or bottom-top<=threshold:continue
        pieces.append(image.crop((0,cursor,image.width,top)))
        pieces.append(Image.new('RGB',(image.width,kept),'white'))
        removed.append([top+kept,bottom]);cursor=bottom
    pieces.append(image.crop((0,cursor,image.width,image.height)))
    if not removed:return image,[]
    result=Image.new('RGB',(image.width,sum(p.height for p in pieces)),'white');y=0
    for part in pieces:result.paste(part,(0,y));y+=part.height
    return result,removed

def prepare_material(path,item,answer=False):
    path=Path(path);raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest()
    with Image.open(path) as opened:image=opened.convert('RGB')
    guide=item.get('answer_layout' if answer else 'question_layout',guides().get(digest,{}))
    if guide and guide.get('sha256')!=digest:raise ValueError('Layout review is stale: asset hash changed')
    original_height=image.height
    protected=[(rectangle(v,*image.size)[1],rectangle(v,*image.size)[3]) for v in guide.get('keep_together',[])]
    draw=ImageDraw.Draw(image);masks=guide.get('masks',[])
    for value in masks:draw.rectangle(rectangle(value,*image.size),fill='white')
    # Crop only reviewed furniture. Never infer a semantic crop from low ink ratio.
    if guide.get('crop'):
        rect=rectangle(guide['crop'],*image.size);image=image.crop(rect)
        protected=[(max(0,t-rect[1]),min(image.height,b-rect[1])) for t,b in protected if b>rect[1] and t<rect[3]]
    gray=image.convert('L');box=gray.point(lambda x:255 if x<250 else 0).getbbox()
    trim=None
    if box:
        trim=[0,max(0,box[1]-6),image.width,min(image.height,box[3]+6)]
        image=image.crop(trim)
        protected=[(max(0,t-trim[1]),min(image.height,b-trim[1])) for t,b in protected if b>trim[1] and t<trim[3]]
    image,removed=compact_white(image,answer)
    def mapped(y):return y-sum(max(0,min(y,b)-t) for t,b in removed)
    protected=[(mapped(t),mapped(b)) for t,b in protected]
    return image,{'protected_ranges':protected,'sha256':digest,'reviewed_geometry':bool(guide),'masks':masks,'crop':guide.get('crop'),'vertical_trim':trim,'white_rows_removed':removed,'prepared_size':list(image.size)}


def safe_white_bands(image,protected):
    bands=white_runs(image)
    for a,z in protected:
        pieces=[]
        for t,b in bands:
            if b<=a or t>=z:pieces.append((t,b))
            else:
                if t<a:pieces.append((t,a))
                if b>z:pieces.append((z,b))
        bands=pieces
    return [(int(t),int(b)) for t,b in bands if b-t>=6]
