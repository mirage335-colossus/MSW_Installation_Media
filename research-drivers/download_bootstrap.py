import pathlib,json,urllib.request,hashlib,concurrent.futures,subprocess,re
ROOT=pathlib.Path(__file__).resolve().parent
DL=ROOT/'packages';DL.mkdir(exist_ok=True)
OUT=ROOT/'extracted'/'bootstrap';OUT.mkdir(exist_ok=True,parents=True)
items=json.loads((ROOT/'bootstrap-candidates.json').read_text());keep=[];skipped=[]
for d in items:
 title=d.get('title','').lower()
 if re.search(r'firmware|wireless wan|wwan|fibocom|quectel|graphics|\bnpu\b|neural processing|total storage encryption|smart standby|static power reduction',title):
  skipped.append(d);continue
 if not d.get('files'):skipped.append(d);continue
 keep.append(d)
# Exact binary dedupe: retain coverage and descriptor provenance.
unique={}
for d in keep:
 key=tuple((f['name'],f['sha256']) for f in d['files'])
 if key not in unique:unique[key]=d
 else:
  u=unique[key];u['types']=sorted(set(u['types']+d['types']));u['models']=sorted(set(u['models']+d['models']));u['catalogs']=sorted(set(u['catalogs']+d['catalogs']))
keep=list(unique.values())
(ROOT/'bootstrap-selected.json').write_text(json.dumps(keep,indent=2));(ROOT/'bootstrap-excluded.json').write_text(json.dumps(skipped,indent=2))
print('SELECTED',len(keep),'PACKAGES',sum(f['size'] for d in keep for f in d['files'])//1024**2,'MiB',flush=True)
def run(d):
 try:
  for f in d['files']:
   p=DL/f['name'];h=hashlib.sha256()
   if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest().lower()==f['sha256'].lower():pass
   else:
    with urllib.request.urlopen(f['url'],timeout=120) as r,p.with_suffix(p.suffix+'.part').open('wb') as out:
     while b:=r.read(2**20):out.write(b);h.update(b)
    if h.hexdigest().lower()!=f['sha256'].lower():raise ValueError('CHECKSUM MISMATCH')
    p.with_suffix(p.suffix+'.part').rename(p)
  out=OUT/d['id'];out.mkdir(exist_ok=True)
  with (out/'extraction.log').open('w') as log:
   r=subprocess.run(['innoextract','-s','-d',str(out),str(p)],stdout=log,stderr=subprocess.STDOUT)
   if r.returncode:r=subprocess.run(['7z','x','-y','-o'+str(out),str(p)],stdout=log,stderr=subprocess.STDOUT)
  infs=list(out.rglob('*.inf'))+list(out.rglob('*.INF'))
  return d['id'],len(infs),r.returncode
 except Exception as e:return d['id'],'ERROR',str(e)
res=[]
for r in concurrent.futures.ThreadPoolExecutor(max_workers=8).map(run,keep):
 res.append(r);print(*r,flush=True)
(ROOT/'download-extraction-results.json').write_text(json.dumps(res,indent=2))
