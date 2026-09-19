from pathlib import Path
import json,shutil,re,hashlib,collections
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'bootstrap-drivers';OUT.mkdir(exist_ok=True)
selected=json.loads((ROOT/'bootstrap-selected.json').read_text());results=json.loads((ROOT/'download-extraction-results.json').read_text())
errors=[r for r in results if r[1]=='ERROR' or r[2]!=0]
noinf={r[0] for r in results if r[1]==0}
selected=[d for d in selected if d['id'] not in noinf and d['id']!='r2ifc03w']
if errors:raise SystemExit('Unresolved extraction: '+str(errors))

def text(p):
 b=p.read_bytes()
 if b.startswith((b'\xff\xfe',b'\xfe\xff')):return b.decode('utf-16',errors='replace')
 return b.decode('cp1252',errors='replace')

def normalize_root(raw):
 entries=[p for p in raw.iterdir() if p.name!='extraction.log']
 if len(entries)==1 and entries[0].is_dir():return entries[0]
 return raw

sources=[]
for d in selected:
 raw=normalize_root(ROOT/'extracted'/'bootstrap'/d['id']);dest=OUT/d['id'];shutil.copytree(raw,dest,dirs_exist_ok=True) if not dest.exists() else None
 if (dest/'extraction.log').exists():(dest/'extraction.log').unlink()
 sources.append({**d,'staged_path':str(dest.relative_to(ROOT)),'payload_root':str(raw.relative_to(ROOT))})
# E485 chipset components only available inside AMD video bundle.
base=ROOT/'extracted'/'E485'/'code$GetExtractPath$'/'Video'/'R0UA112W'
for label,rel in [('e485-amdpsp','AMDPSP/WT64A'),('e485-smbus','SBDrv/SMBus/WT64A')]:
 raw=base/rel;dest=OUT/label;shutil.copytree(raw,dest,dirs_exist_ok=True) if not dest.exists() else None
 sources.append({'id':label,'title':'E485 AMD chipset component from SCCM pack','date':'2021-05-24','version':'R0UA112W','types':['20KU'],'models':['ThinkPad E485'],'staged_path':str(dest.relative_to(ROOT)),'files':[{'url':'https://download.lenovo.com/pccbbs/mobiles/tp_e485_e585_w1064_202105.exe','name':'tp_e485_e585_w1064_202105.exe','sha256':'f3d9b92f47e606bd20e4e4b8921da8e220095f7b4a85433ee6c46d7055f79777'}]})

infs=[];classes=collections.Counter();hws=set();excluded=[]
for p in sorted(OUT.rglob('*')):
 if p.suffix.lower()!='.inf':continue
 s=text(p)
 def value(key):
  m=re.search(r'^\s*'+re.escape(key)+r'\s*=\s*([^;\r\n]+)',s,re.I|re.M);return m.group(1).strip().strip('"') if m else None
 cls=value('Class')
 if cls and cls.lower()=='firmware':excluded.append(str(p.relative_to(OUT)));p.unlink();continue
 hw=sorted(set(re.findall(r'(?:PCI|USB|ACPI|HID|HDAUDIO|ROOT|SWC)\\[^\s,;"\r\n]+',s,re.I)))
 hws.update(x.upper() for x in hw);classes[cls or 'unknown']+=1
 infs.append({'path':str(p.relative_to(OUT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'class':cls,'provider':value('Provider'),'driverver':value('DriverVer'),'catalog':value('CatalogFile'),'hardware_ids':hw})

(ROOT/'driver-manifest.json').write_text(json.dumps({'retrieved':'2026-09-18','sources':sources,'infs':infs,'excluded_firmware_infs':excluded,'non_inf_packages_omitted':sorted(noinf)},indent=2))
(ROOT/'hardware-ids.txt').write_text('\n'.join(sorted(hws))+'\n')
(ROOT/'source-checksums.sha256').write_text('\n'.join(sorted(set(f['sha256'].lower()+'  '+f['name'] for d in sources for f in d['files'])))+'\n')
lines=['Model types\tPackages\tNetwork packages']
types=sorted(set(t for d in sources for t in d['types']))
for t in types:
 src=[d for d in sources if t in d['types']];n=[d['id'] for d in src if any(x['class'] and x['class'].lower()=='net' and x['path'].startswith(d['id']+'/') for x in infs)]
 lines.append(t+'\t'+','.join(d['id'] for d in src)+'\t'+','.join(n))
(ROOT/'model-coverage.tsv').write_text('\n'.join(lines)+'\n')
bytes_=sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())
summary={'packages':len(sources),'infs':len(infs),'classes':dict(classes),'hardware_ids':len(hws),'bytes':bytes_,'types':types,'excluded_firmware_infs':excluded}
(ROOT/'bootstrap-summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
