from pathlib import Path
import xml.etree.ElementTree as E,urllib.request,concurrent.futures,hashlib,json,re
root=Path(__file__).resolve().parent;md=root/'metadata';seen={}
for p in md.glob('*Win11.xml'):
 for x in E.parse(p).getroot():
  url=x.findtext('location');d=seen.setdefault(url,{'url':url,'sha':x.findtext('checksum'),'catalogs':[],'category':x.findtext('category')});d['catalogs'].append(p.name)
def fetch(d):
 try:
  p=md/d['url'].rsplit('/',1)[-1]
  b=p.read_bytes() if p.exists() else urllib.request.urlopen(d['url'],timeout=60).read()
  assert hashlib.sha256(b).hexdigest().lower()==d['sha'].lower()
  p.write_bytes(b);t=E.fromstring(b)
  d.update(id=t.get('id'),title=t.findtext('Title/Desc'),date=t.findtext('ReleaseDate'))
  return d
 except Exception as e:return {**d,'error':str(e)}
rs=list(concurrent.futures.ThreadPoolExecutor(max_workers=10).map(fetch,seen.values()))
(root/'all-descriptor-audit.json').write_text(json.dumps(rs,indent=2))
for d in rs:
 if d.get('error') or re.search('rapid|\bvmd\b|iastor|\brst\b|\braid\b|storage|ahci',d.get('title',''),re.I):print(d.get('title') or d.get('error'),d['category'],','.join(d['catalogs']))
print('TOTAL',len(rs),'ERRORS',len([x for x in rs if x.get('error')]))
