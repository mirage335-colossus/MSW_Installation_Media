#!/bin/bash
# Build and verify a regular raw image. This script never accepts a target device.
set -euo pipefail
umask 077
export PATH=/usr/sbin:/usr/bin:/sbin:/bin

if (( EUID == 0 )); then
  printf 'Run as the ordinary workspace user; only loop operations use sudo -n.\n' >&2
  exit 2
fi
if (( $# != 1 )); then
  printf 'Usage: %s NEW_OUTPUT_DIRECTORY\n' "$0" >&2
  exit 2
fi

base=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd -P)
stage="$base/staging"
ready="$base/verification/validation-ready.json"
helper="$base/scripts/verify-release-payload.py"
for tool in python3 sudo sfdisk losetup mkfs.vfat mount umount mountpoint fsck.vfat rsync truncate sync tee; do
  command -v "$tool" >/dev/null || { printf 'Required command missing: %s\n' "$tool" >&2; exit 2; }
done
output=$(python3 - "$1" "$stage" <<'PY'
from pathlib import Path
import sys
output = Path(sys.argv[1]).absolute()
if output.exists() or output.is_symlink():
    raise SystemExit('Output directory must not already exist.')
output = output.resolve()
stage = Path(sys.argv[2]).resolve()
if output == stage or stage in output.parents or output in stage.parents:
    raise SystemExit('Output directory cannot contain staging or be inside it.')
if any(ord(char) < 32 or ord(char) == 127 for char in str(output)):
    raise SystemExit('Output directory cannot contain control characters.')
print(output)
PY
)
mkdir -p -- "$(dirname -- "$output")"
mkdir -- "$output"
mount_path="$output/mount"
partial="$output/MSW11-Lenovo-x64.partial.img"
final="$output/MSW11-Lenovo-x64.img"
loop_device=''
complete=0
printf 'Build is incomplete. A .partial.img is not a release artifact.\n' > "$output/INCOMPLETE.txt"
exec > >(tee -a "$output/build.log") 2>&1

cleanup() {
  status=$?
  trap - EXIT
  set +e
  if mountpoint -q "$mount_path"; then
    sudo -n umount "$mount_path" || status=1
  fi
  if [[ -n "$loop_device" ]]; then
    if [[ "$loop_device" =~ ^/dev/loop[0-9]+$ ]] && ! mountpoint -q "$mount_path"; then
      sudo -n losetup --detach "$loop_device" || status=1
    else
      printf 'Cleanup could not safely detach the allocated loop: %s\n' "$loop_device" >&2
      status=1
    fi
  fi
  if (( status != 0 || complete != 1 )); then
    printf 'Build incomplete (exit %s). Inspect build.log; partial files are not ready to flash.\n' "$status" \
      > "$output/INCOMPLETE.txt"
    printf 'Release build incomplete; retained evidence in %s\n' "$output" >&2
    (( status != 0 )) || status=1
  fi
  exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

test -f "$ready" && test ! -L "$ready"
test -f "$stage/SHA256SUMS.txt" && test ! -L "$stage/SHA256SUMS.txt"
cp --no-dereference "$ready" "$output/source-validation-ready.json"
cp --no-dereference "$stage/SHA256SUMS.txt" "$output/SHA256SUMS.source.txt"
printf 'Verifying frozen staging and prior account-test evidence...\n'
python3 "$helper" payload --root "$stage" \
  --ready "$output/source-validation-ready.json" --manifest "$output/SHA256SUMS.source.txt" \
  --report "$output/source-preflight.json"

# Create only a fresh regular file in the exclusive output directory.
(set -o noclobber; : > "$partial")
truncate -s 61991813120 "$partial"
printf 'label: dos\nunit: sectors\n\nstart=2048, size=121075712, type=c, bootable\n' \
  | sfdisk --no-reread --no-tell-kernel "$partial" > "$output/partition-create.log"
python3 "$helper" geometry --image "$partial" --partition-only --report "$output/partition-preflight.json"
mkdir -- "$mount_path"

attach_loop() {
  mode=$1
  args=(--find --show --partscan --sector-size 512)
  verify_args=()
  if [[ "$mode" == read ]]; then
    args+=(--read-only)
    verify_args+=(--read-only)
  fi
  loop_device=$(sudo -n losetup "${args[@]}" "$partial")
  [[ "$loop_device" =~ ^/dev/loop[0-9]+$ ]] || { printf 'Unexpected allocated device.\n' >&2; return 1; }
  # Logs belong to the invoking user; only device inspection runs under sudo.
  # shellcheck disable=SC2024
  sudo -n losetup --list --json --output NAME,BACK-FILE,BACK-INO,OFFSET,SIZELIMIT,RO,LOG-SEC \
    "$loop_device" > "$output/loop-$mode.json"
  python3 "$helper" loop --device "$loop_device" --image "$partial" \
    --metadata "$output/loop-$mode.json" "${verify_args[@]}"
  partition="${loop_device}p1"
  for _ in {1..50}; do
    [[ -b "$partition" ]] && return 0
    sleep 0.1
  done
  printf 'Allocated loop partition did not appear: %s\n' "$partition" >&2
  return 1
}

detach_loop() {
  sudo -n losetup --detach "$loop_device"
  loop_device=''
}

attach_loop write
printf 'Formatting the verified image-backed loop partition...\n'
# The log is user-owned even though formatting the allocated loop requires sudo.
# shellcheck disable=SC2024
sudo -n mkfs.vfat -F 32 -S 512 -s 64 -g 255/63 -h 2048 -n MSW11LENOVO "$partition" > "$output/format.log"
sudo -n mount -t vfat -o "uid=$(id -u),gid=$(id -g),umask=022,utf8=1,nosuid,nodev,noexec" \
  "$partition" "$mount_path"
python3 - "$mount_path" "$output/source-preflight.json" <<'PY'
import json, os, sys
info = os.statvfs(sys.argv[1])
needed = json.load(open(sys.argv[2]))['allocation_bound_bytes']
if needed >= info.f_bavail * info.f_frsize:
    raise SystemExit('Cluster-rounded payload exceeds formatted image capacity.')
PY
rsync -rt --info=stats2 -- "$stage/" "$mount_path/"
sync -f "$mount_path"
sudo -n umount "$mount_path"
detach_loop
sync -f "$partial"

printf 'Reopening image read-only for complete readback verification...\n'
attach_loop read
sudo -n mount -t vfat -o "ro,uid=$(id -u),gid=$(id -g),umask=022,utf8=1,nosuid,nodev,noexec" \
  "$partition" "$mount_path"
python3 "$helper" payload --root "$mount_path" \
  --ready "$output/source-validation-ready.json" --manifest "$output/SHA256SUMS.source.txt" \
  --reference-layout "$output/source-preflight.json" --report "$output/readback-verification.json"
sudo -n umount "$mount_path"
# Preserve filesystem-check output as the invoking user, not as root.
# shellcheck disable=SC2024
sudo -n fsck.vfat -n "$partition" > "$output/filesystem-check.log" 2>&1
detach_loop
rmdir -- "$mount_path"
python3 "$helper" geometry --image "$partial" --report "$output/geometry-verification.json"
python3 "$helper" release --image "$partial" --ready "$output/source-validation-ready.json" \
  --source-report "$output/source-preflight.json" --readback-report "$output/readback-verification.json" \
  --fsck-log "$output/filesystem-check.log" \
  --report "$output/release-image.json.partial" --checksum "$output/MSW11-Lenovo-x64.img.sha256.partial"

# The image receives its public name only after every verification and full hash succeeds.
mv -- "$output/MSW11-Lenovo-x64.img.sha256.partial" "$output/MSW11-Lenovo-x64.img.sha256"
mv -- "$output/release-image.json.partial" "$output/release-image.json"
mv -- "$partial" "$final"
sync -f "$final"
rm -- "$output/INCOMPLETE.txt"
complete=1
printf 'Verified release image: %s\n' "$final"
printf 'No boot smoke test or physical-device functionality test was performed by this build.\n'
