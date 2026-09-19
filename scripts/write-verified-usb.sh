#!/bin/bash
set -euo pipefail
base=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
target=/dev/disk/by-id/usb-Kingston_DataTraveler_3.0_4CEDFB74A32C1A70790301C3-0:0
mount_path="$base/verification/physical-usb-mount"
test -f "$base/verification/validation-ready.json"
test -f "$base/staging/SHA256SUMS.txt"
test -f "$base/staging/efi/boot/bootx64.efi"
test -f "$base/staging/sources/install.swm"
test -f "$base/staging/profiles/local.xml"
test -d "$base/staging/\$WinPEDriver\$"
(cd "$base/staging" && sha256sum -c SHA256SUMS.txt) > "$base/verification/staging-prewrite-sha256.txt"
python3 - "$target" "$base" <<'PY'
import hashlib,json,os,subprocess,sys
from pathlib import Path
target,base=sys.argv[1:]
ready=json.load(open(base+'/verification/validation-ready.json'))
assert ready['account_validation']=='passed', 'Account validation not complete'
assert hashlib.sha256((Path(base)/'staging/SHA256SUMS.txt').read_bytes()).hexdigest()==ready['sha256_manifest_sha256'], 'Final checksum manifest changed'
assert hashlib.sha256((Path(base)/'staging/Documentation/driver-manifest.json').read_bytes()).hexdigest()==ready['final_driver_manifest_sha256'], 'Final driver manifest changed'
for name,expected in ready['tested_file_sha256'].items():
    with (Path(base)/'staging'/name).open('rb') as f:
        assert hashlib.file_digest(f,'sha256').hexdigest()==expected, 'Tested content changed: '+name
files=[p for p in (Path(base)/'staging').rglob('*') if p.is_file()]
assert all(p.stat().st_size < 2**32 for p in files), 'File exceeds FAT32 limit'
assert sum(((p.stat().st_size+32767)//32768)*32768 for p in files) < 60_000_000_000, 'Payload exceeds target capacity'
info=json.loads(subprocess.check_output(['lsblk','--tree','-b','-J','-o','PATH,SIZE,MODEL,SERIAL,TRAN,RM,TYPE,MOUNTPOINTS',target]))['blockdevices']
assert len(info)==1
d=info[0]
assert d['serial']=='4CEDFB74A32C1A70790301C3'
assert d['size']==61991813120
assert d['type']=='disk' and d['tran']=='usb' and d['rm'] is True
assert d['model'].strip()=='DataTraveler 3.0'
def check_unmounted(node):
    assert not any(node.get('mountpoints') or []), 'Target is mounted'
    for child in node.get('children',[]): check_unmounted(child)
check_unmounted(d)
assert os.path.realpath(target) != '/dev/nvme0n1'
print('Verified USB target:',d['path'],d['model'],d['serial'],d['size'],flush=True)
PY
mkdir -p "$mount_path"
cleanup() {
  if mountpoint -q "$mount_path"; then sudo -n umount "$mount_path"; fi
}
trap cleanup EXIT
printf 'label: dos\nunit: sectors\n\nstart=2048, type=c, bootable\n' | sudo -n sfdisk --wipe always --wipe-partitions always "$target"
sudo -n udevadm settle
test -b "${target}-part1"
sudo -n mkfs.vfat -F 32 -s 64 -n MSW11LENOVO "${target}-part1"
sudo -n mount -o "uid=$(id -u),gid=$(id -g),umask=022,nosuid,nodev,noexec" "${target}-part1" "$mount_path"
rsync -rt --info=progress2 "$base/staging/" "$mount_path/"
sync -f "$mount_path"
sudo -n umount "$mount_path"
sudo -n blockdev --flushbufs "$target"
sudo -n mount -o ro,nosuid,nodev,noexec "${target}-part1" "$mount_path"
(cd "$mount_path" && sha256sum -c SHA256SUMS.txt) > "$base/verification/usb-readback-sha256.txt"
sudo -n umount "$mount_path"
sudo -n fsck.vfat -n "${target}-part1" > "$base/verification/usb-filesystem-check.txt"
sudo -n fdisk -l "$target" > "$base/verification/usb-final-partition-table.txt"
printf 'USB written, flushed, read back, checksum-verified and unmounted.\n'
