"""Rebuild reviewed subparts from hash-bound originals; keep originals read-only."""
from pathlib import Path
import hashlib,json,copy,re
from PIL import Image
from builtin_bank import ensure_assets

RES=Path(__file__).resolve().parents[1]/'resources'

def all_recipes(workspace=None,course=None):
    rows=json.loads((RES/'excerpt-recipes.json').read_text())['recipes']
    if workspace and course:
        folder=Path(workspace)/course/'reviewed-excerpt-recipes'
        if folder.exists():rows+=[json.loads(p.read_text()) for p in sorted(folder.glob('*.json'))]
    return list({r['id']:r for r in rows}.values())

def get_recipe(ident,workspace=None,course=None):
    return next((r for r in all_recipes(workspace,course) if r['id']==ident),None)

def materialize(workspace,recipe,parent):
    if not re.fullmatch(r'[A-Za-z0-9_-]+',recipe['id']) or recipe['id']==parent['id']:raise ValueError('A safe independent excerpt ID is required')
    if recipe['original_id']!=parent['id']:raise ValueError('Excerpt parent does not match')
    ensure_assets([parent]);row={**copy.deepcopy(parent),**recipe}
    dest=Path(workspace)/recipe['course']/'excerpts'/recipe['id'];dest.mkdir(parents=True,exist_ok=True)
    for side in ['question','answer']:
        source=Path(parent[side+'_image']);digest=hashlib.sha256(source.read_bytes()).hexdigest()
        if digest!=recipe[side+'_source_sha256']:raise ValueError('Excerpt source changed; re-review required')
        target=dest/(side+'.png')
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()==recipe.get(side+'_output_sha256'):row[side+'_image']=str(target);continue
        image=Image.open(source).convert('RGB');parts=[]
        for l,t,r,b in recipe[side+'_boxes']:
            if not(0<=l<r<=1 and 0<=t<b<=1):raise ValueError('Invalid excerpt crop')
            parts.append(image.crop((round(l*image.width),round(t*image.height),round(r*image.width),round(b*image.height))))
        if len(parts)==1:result=parts[0]
        else:
            result=Image.new('RGB',(max(p.width for p in parts),sum(p.height for p in parts)+20*(len(parts)-1)),'white');y=0
            for part in parts:result.paste(part,(0,y));y+=part.height+20
        result.save(target)
        if recipe.get(side+'_output_sha256') and hashlib.sha256(target.read_bytes()).hexdigest()!=recipe[side+'_output_sha256']:raise ValueError('Rebuilt excerpt differs from inspected material')
        row[side+'_image']=str(target)
    for key in ['source_kind','question_asset','answer_asset']:row.pop(key,None)
    row['corrected_marks']=row['marks'];row['kind']='structured';row['excerpt']=True
    return row
