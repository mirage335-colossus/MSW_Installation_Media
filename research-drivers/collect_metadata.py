import pathlib,json,urllib.request,hashlib,concurrent.futures,xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parent
DIR=ROOT/'metadata';DIR.mkdir(exist_ok=True)
packs=[p for p in json.loads((ROOT/'latest-packs.json').read_text()) if not any('L14P' in x for x in p['models'])]
def get(url,path,expected=None):
 if path.exists():data=path.read_bytes()
 else:
  data=urllib.request.urlopen(url,timeout=90).read();path.write_bytes(data)
 if expected and hashlib.sha256(data).hexdigest().lower()!=expected.lower():raise ValueError('HASH MISMATCH '+url)
 return data
def model(p):
 mt=p['types'][0].lower();os='Win10' if mt=='20ku' else 'Win11';url=f'https://download.lenovo.com/catalog/{mt}_{os}.xml'
 try:
  tree=ET.fromstring(get(url,DIR/f'{mt}_{os}.xml'))
  return [(x.findtext('location'),x.findtext('checksum'),x.findtext('category'),p['models'],p['types'],url) for x in tree]
 except Exception as e:return [(None,str(e),mt,[],[],url)]
items={}
for result in concurrent.futures.ThreadPoolExecutor(max_workers=8).map(model,packs):
 for url,h,cat,models,types,catalog in result:
  if url is None:print('MODEL FAILED',h,cat);continue
  if not any(x in cat.lower() for x in ('network','chipset','storage','mouse','keyboard','usb','power management','input')):continue
  if any(x in cat.lower() for x in ('wwan','wan ')):continue
  if url not in items:items[url]={'metadata_url':url,'metadata_sha256':h,'category':cat,'models':[],'types':[],'catalogs':[]}
  d=items[url];d['models']=sorted(set(d['models']+models));d['types']=sorted(set(d['types']+types));d['catalogs']=sorted(set(d['catalogs']+[catalog]))
def desc(d):
 try:
  tree=ET.fromstring(get(d['metadata_url'],DIR/d['metadata_url'].rsplit('/',1)[-1],d['metadata_sha256']))
  d['id']=tree.get('id');d['title']=tree.findtext('Title/Desc');d['version']=tree.get('version');d['date']=tree.findtext('ReleaseDate')
  files=[]
  for item in tree.findall('Files/Installer/File'):
   name=item.findtext('Name');files.append({'url':d['metadata_url'].rsplit('/',1)[0]+'/'+name,'name':name,'sha256':item.findtext('CRC'),'size':int(item.findtext('Size') or 0)})
  d['files']=files;d['extract_command']=tree.findtext('ExtractCommand')
  return d
 except Exception as e:return {**d,'error':str(e)}
allitems=list(concurrent.futures.ThreadPoolExecutor(max_workers=8).map(desc,items.values()))
(ROOT/'bootstrap-candidates.json').write_text(json.dumps(allitems,indent=2))
for d in allitems:
 print(d.get('id'),sum(f['size'] for f in d.get('files',[]))//1024**2,'MiB',d.get('date'),d.get('title') or d.get('error'),','.join(d['types']))
