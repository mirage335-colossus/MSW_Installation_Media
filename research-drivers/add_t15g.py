from pathlib import Path
import json,urllib.request,hashlib,concurrent.futures,subprocess,xml.etree.ElementTree as E
root=Path(__file__).resolve().parent
ids={'n2idg13w_p','n4ody12w_w10w11','n30ta05w','n30hd03w','n30ch02w','n30tr02w','n30ac02w','n2xst13w','n30wb04w','n2ita11w','n30rw03w','nz7w809w','n30md15w','n1fupa7w_w10w11','n4bku13w_w10w11'}
all_=json.loads((root/'t15g-all-descriptors.json').read_text());wanted=[d for d in all_ if d['id'] in ids];assert len(wanted)==len(ids)
existing=json.loads((root/'bootstrap-selected.json').read_text());key=lambda d:tuple((f['name'],f['sha256'].lower()) for f in d['files']);index={key(d):d for d in existing};new=[]
for d in wanted:
 k=key(d)
 if k in index:
  old=index[k]
  for name in ('models','types','catalogs'):old[name]=sorted(set(old[name]+d[name]))
  old.setdefault('additional_metadata',[]).append({'url':d['metadata_url'],'sha256':d['metadata_sha256']})
 else:new.append(d)
def fetch(d):
 for f in d['files']:
  p=root/'packages'/f['name'];b=urllib.request.urlopen(f['url'],timeout=120).read();assert hashlib.sha256(b).hexdigest().lower()==f['sha256'].lower();p.write_bytes(b)
 out=root/'extracted'/'bootstrap'/d['id'];out.mkdir(exist_ok=True)
 with (out/'extraction.log').open('w') as log:subprocess.run(['innoextract','-s','-d',str(out),str(p)],stdout=log,stderr=subprocess.STDOUT,check=True)
 infs=[x for x in out.rglob('*') if x.suffix.lower()=='.inf']
 return [d['id'],len(infs),0]
results=list(concurrent.futures.ThreadPoolExecutor(max_workers=6).map(fetch,new))
(root/'bootstrap-selected.json').write_text(json.dumps(existing+new,indent=2))
oldresults=json.loads((root/'download-extraction-results.json').read_text());oldresults=[x for x in oldresults if x[0] not in {d['id'] for d in new}]+results;(root/'download-extraction-results.json').write_text(json.dumps(oldresults,indent=2))
(root/'t15g-selected.json').write_text(json.dumps(wanted,indent=2));(root/'t15g-excluded.json').write_text(json.dumps([d for d in all_ if d['id'] not in ids],indent=2))
for result in results:print(*result,flush=True)
# Preserve exact current deployment-catalog family mapping.
models=[]
for m in E.parse(root/'catalogv2.xml').getroot():
 types=[x.text for x in m.findall('Types/Type')]
 if not {'20UR','20US'}&set(types):continue
 models.append({'model':m.attrib,'types':types,'packages':[{'kind':p.tag,**p.attrib,'url':p.text} for p in m if p.tag not in ('Types','BIOS')]})
(root/'t15g-sccm-catalog.json').write_text(json.dumps(models,indent=2))
