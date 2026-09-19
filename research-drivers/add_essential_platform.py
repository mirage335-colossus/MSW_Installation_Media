from pathlib import Path
import json,xml.etree.ElementTree as E,urllib.request,concurrent.futures,hashlib,subprocess
root=Path(__file__).resolve().parent;ids={'r2iai03w','r2ipp03w','r2upp05w','r1jhe07w','r1xhd03w','r3ehd02w','nzbmt04w'}
all_=json.loads((root/'all-descriptor-audit.json').read_text());old=json.loads((root/'bootstrap-selected.json').read_text());pkgs=json.loads((root/'latest-packs.json').read_text())
new=[]
for a in all_:
 if a.get('id') not in ids:continue
 t=E.parse(root/'metadata'/a['url'].rsplit('/',1)[-1]).getroot();types=set();models=set()
 for c in a['catalogs']:
  type_=c[:4].upper()
  for p in pkgs:
   if type_ in p['types']:types.update(p['types']);models.update(p['models'])
 files=[]
 for f in t.findall('Files/Installer/File'):
  n=f.findtext('Name');files.append({'url':a['url'].rsplit('/',1)[0]+'/'+n,'name':n,'sha256':f.findtext('CRC'),'size':int(f.findtext('Size'))})
 new.append({'id':a['id'],'metadata_url':a['url'],'metadata_sha256':a['sha'],'category':a['category'],'title':a['title'],'version':t.get('version'),'date':a['date'],'types':sorted(types),'models':sorted(models),'catalogs':['https://download.lenovo.com/catalog/'+c for c in a['catalogs']],'files':files,'extract_command':t.findtext('ExtractCommand')})
def dl(d):
 for f in d['files']:
  p=root/'packages'/f['name'];b=urllib.request.urlopen(f['url'],timeout=90).read();assert hashlib.sha256(b).hexdigest().lower()==f['sha256'].lower();p.write_bytes(b)
 out=root/'extracted'/'bootstrap'/d['id'];out.mkdir(exist_ok=True)
 with (out/'extraction.log').open('w') as log:subprocess.run(['innoextract','-s','-d',str(out),str(p)],stdout=log,stderr=subprocess.STDOUT,check=True)
 infs=[p for p in out.rglob('*') if p.suffix.lower()=='.inf'];assert infs
 return [d['id'],len(infs),0]
res=list(concurrent.futures.ThreadPoolExecutor(max_workers=7).map(dl,new));assert len(new)==7
old=[d for d in old if d['id'] not in ids]+new;(root/'bootstrap-selected.json').write_text(json.dumps(old,indent=2))
r=json.loads((root/'download-extraction-results.json').read_text());r=[x for x in r if x[0] not in ids]+res;(root/'download-extraction-results.json').write_text(json.dumps(r,indent=2))
for x in res:print(x)
