"""Build a portable static site without Node or a CDN."""
from pathlib import Path
import json, shutil
ROOT=Path(__file__).resolve().parents[1]
def main():
    data=json.loads((ROOT/'site/data.json').read_text())
    assert data['quality']['reconciled'], 'Reconciliation must pass'
    assert all(f['counts']==sorted(f['counts'],reverse=True) for f in data['funnels'])
    target=ROOT/'dist'; target.mkdir(exist_ok=True)
    shutil.copytree(ROOT/'outputs/finance',target/'finance',dirs_exist_ok=True)
    for name in ['index.html','style.css','app.js','data.json']: shutil.copy2(ROOT/'site'/name,target/name)
    shutil.copytree(ROOT/'docs',target/'docs',dirs_exist_ok=True)
    (target/'.nojekyll').touch()
    print('Built dist/ from validated aggregate snapshot; source = '+data['source'])
if __name__=='__main__': main()
