#!/usr/bin/env python3
"""Prepare Microsoft media, preserving interactive disk and account choices."""
import hashlib
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

base = Path(__file__).resolve().parent.parent
iso = base/'downloads/Win11_25H2_English_x64_v2.iso'
expected = '768984706b909479417b2368438909440f2967ff05c6a9195ed2667254e465e3'
with iso.open('rb') as f:
    actual = hashlib.file_digest(f, 'sha256').hexdigest()
if actual != expected:
    raise SystemExit('Microsoft ISO SHA256 mismatch; refusing to build.')
stage = base/'staging'
if (stage/'sources').exists() and '--resume' not in sys.argv:
    raise SystemExit('Staging already contains media; inspect before rebuilding.')
logs = base/'verification'
def run(args, log):
    print('Running', args[0], flush=True)
    with (logs/log).open('w') as f:
        subprocess.run(args, check=True, stdout=f, stderr=subprocess.STDOUT)
if '--resume' not in sys.argv:
    run(['7z','x','-y',f'-o{stage}',str(iso)], 'iso-extraction.log')
run(['wimlib-imagex','info',str(stage/'sources/install.wim')], 'install-image-info.txt')
run(['wimlib-imagex','info',str(stage/'sources/boot.wim')], 'boot-image-info.txt')
original = base/'verification/original-boot-files'
original.mkdir(exist_ok=True)
run(['wimlib-imagex','extract',str(stage/'sources/boot.wim'),'2',
     'Windows/System32/winpeshl.ini',f'--dest-dir={original}','--nullglob'], 'original-winpeshl.log')
for name in ['MediaSetup.cmd','winpeshl.ini']:
    source = base/'research-accounts'/name
    with subprocess.Popen(['wimlib-imagex','update',str(stage/'sources/boot.wim'),'2'],
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True) as p:
        out,_ = p.communicate(f'add "{source}" "/Windows/System32/{name}"\n')
        (logs/f'boot-add-{name}.log').write_text(out)
        if p.returncode:
            raise SystemExit(f'boot.wim update failed: {name}')
shutil.copytree(base/'research-accounts/profiles',stage/'profiles',dirs_exist_ok=True)
for name in ['MSW11-MEDIA.ID','Enable-E485-Compatibility.cmd']:
    shutil.copyfile(base/'research-accounts'/name,stage/name)
helper=(base/'scripts/Install-Drivers.cmd').read_text()
(stage/'Install-Drivers.cmd').write_bytes(helper.replace('\n','\r\n').encode('ascii'))
for profile in (stage/'profiles').glob('*.xml'):
    doc=ET.parse(profile)
    forbidden={'DiskConfiguration','ImageInstall','UserAccounts','AutoLogon','SkipMachineOOBE','SkipUserOOBE'}
    if any(node.tag.split('}')[-1] in forbidden for node in doc.iter()):
        raise SystemExit('Unexpected unattended action in '+str(profile))
run(['wimlib-imagex','verify',str(stage/'sources/boot.wim')], 'boot-wim-verify.txt')
run(['wimlib-imagex','split',str(stage/'sources/install.wim'),str(stage/'sources/install.swm'),'3800','--check'], 'split-image.log')
run(['wimlib-imagex','verify',str(stage/'sources/install.swm'),f'--ref={stage}/sources/install*.swm'], 'install-swm-verify.txt')
(stage/'sources/install.wim').unlink()
for path in stage.rglob('*'):
    if path.is_file() and path.stat().st_size >= 2**32:
        raise SystemExit('File exceeds FAT32 limit: '+str(path))
print('Microsoft media and account profiles prepared and verified.',flush=True)
