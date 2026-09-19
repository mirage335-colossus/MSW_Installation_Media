set -euo pipefail
release_dir="$PWD/release/r3"
check_dir="$PWD/verification/t1"
image_path="$release_dir/MSW11-Lenovo-x64.img"
mkdir "$check_dir"
python3 - "$release_dir" <<'PY'
from pathlib import Path
import hashlib, json, stat, sys
root = Path(sys.argv[1])
for name in ('INCOMPLETE.txt', 'MSW11-Lenovo-x64.partial.img',
             'release-image.json.partial', 'MSW11-Lenovo-x64.img.sha256.partial'):
    if (root/name).exists() or (root/name).is_symlink():
        raise SystemExit('Incomplete packaging output: '+name)
for name in ('MSW11-Lenovo-x64.img', 'MSW11-Lenovo-x64.img.sha256',
             'release-image.json', 'source-validation-ready.json',
             'SHA256SUMS.source.txt', 'source-preflight.json'):
    if not stat.S_ISREG((root/name).lstat().st_mode):
        raise SystemExit('Need a regular, nonsymlink input: '+name)
report = json.loads((root/'release-image.json').read_text())
if report['status'] != 'verified' or (root/'MSW11-Lenovo-x64.img').stat().st_size != report['image_bytes']:
    raise SystemExit('Release status or image length differs')
expected_line = report['image_sha256']+'  MSW11-Lenovo-x64.img\n'
if (root/'MSW11-Lenovo-x64.img.sha256').read_text() != expected_line:
    raise SystemExit('Image checksum companion differs from release report')
for name, key in [('source-validation-ready.json', 'source_validation_ready_sha256'),
                  ('SHA256SUMS.source.txt', 'source_sha256_manifest_sha256')]:
    if hashlib.sha256((root/name).read_bytes()).hexdigest() != report[key]:
        raise SystemExit('Reference evidence changed: '+name)
print('Reference bundle and declared image length agree.')
PY
(cd "$release_dir" && sha256sum -c MSW11-Lenovo-x64.img.sha256) \
  > "$check_dir/image-sha256.txt" 2>&1
python3 scripts/verify-release-payload.py geometry --image "$image_path" \
  --report "$check_dir/geometry.json"

set -euo pipefail
mount_path="$check_dir/image-mount"
mkdir "$mount_path"
image_loop=''
cleanup_image_check() {
  status=$?
  trap - EXIT
  set +e
  if mountpoint -q "$mount_path"; then sudo -n umount "$mount_path" || status=1; fi
  if test -n "$image_loop"; then
    if mountpoint -q "$mount_path"; then status=1
    else sudo -n losetup -d "$image_loop" || status=1; fi
  fi
  exit "$status"
}
trap cleanup_image_check EXIT
image_loop=$(sudo -n losetup --find --show --partscan --read-only --sector-size 512 "$image_path")
sudo -n losetup --list --json --output NAME,BACK-FILE,BACK-INO,OFFSET,SIZELIMIT,RO,LOG-SEC \
  "$image_loop" > "$check_dir/loop-read.json"
python3 scripts/verify-release-payload.py loop --device "$image_loop" --image "$image_path" \
  --metadata "$check_dir/loop-read.json" --read-only
for attempt in {1..50}; do
  test -b "${image_loop}p1" && break
  sleep 0.1
done
test -b "${image_loop}p1"
sudo -n fsck.vfat -n "${image_loop}p1" > "$check_dir/filesystem-check.txt" 2>&1
sudo -n mount -t vfat -o "ro,uid=$(id -u),gid=$(id -g),umask=022,utf8=1,nosuid,nodev,noexec" \
  "${image_loop}p1" "$mount_path"
python3 scripts/verify-release-payload.py payload --root "$mount_path" \
  --ready "$release_dir/source-validation-ready.json" \
  --manifest "$release_dir/SHA256SUMS.source.txt" \
  --reference-layout "$release_dir/source-preflight.json" \
  --report "$check_dir/payload-readback.json" > "$check_dir/payload-readback.txt" 2>&1
sudo -n umount "$mount_path"
sudo -n losetup -d "$image_loop"
image_loop=''
rmdir "$mount_path"
trap - EXIT
