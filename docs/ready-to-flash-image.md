# Build a verified image that can be flashed to USB

This is the final packaging procedure for the Lenovo Windows 11 installer.
Run it after the [rebuild runbook](runbook.md) has produced tested, finalized
`staging/` and `verification/validation-ready.json`. The image contains the
interactive local/Microsoft account menu, Windows Setup, the complete selected
E485/L14/L15/T15g bootstrap driver collection, documentation and checksums.

There are three different artifacts:

| Artifact | Purpose |
| --- | --- |
| Microsoft's source `.iso` | Authentic input to the build; lacks this project's account menu and driver collection. |
| `verification/test-usb.img` | Candidate used during account installation tests, before final evidence and checksums are added. |
| `release/<release-id>/MSW11-Lenovo-x64.img` | Finalized whole-device image, independently read back and checksummed by the release builder. |

Do not rename the earlier test image and call it the release. Finalization changes
staging and does not update that image. The new packaging command is
[build-release-image.sh](../scripts/build-release-image.sh); its verification
helper is [verify-release-payload.py](../scripts/verify-release-payload.py).
Neither takes a physical USB target. Building and boot-testing an image need no
connected flash drive.

The procedure was run on September 19: the finalized image passed complete
readback, filesystem/geometry checks, a read-only boot to the account-choice
menu and a checksum recheck after shutdown. See the
[integration report and evidence](../verification/release-image-2026-09-19/README.md),
including the two failures found and fixed during that testing.

## What must be available first

For a **new build**, complete runbook steps 1–6: recover and verify the official
ISO and vendor inputs, prepare the account launcher/profiles, stage the complete
driver union, build the candidate, perform the account/driver tests, export
evidence, and finalize. A Git clone excludes the large inputs and is not enough
by itself. Use a short isolated run root as described there.

For a **new package of the identical completed September 18 staging tree**, use
the existing final manifest and dated validation record. This preserves their
scope: Home/local desktop while offline; Pro/online Microsoft sign-in form;
separate acceptance of the later T15g additions. Packaging does not retest live
OOBE, authenticate a cloud account, or test real laptop devices. Record this as
repackaging the existing release, not a new Windows installation test.

Use the runbook's Linux host dependencies, including Python 3.11+, util-linux
(`sfdisk`, `losetup`, `mount`), dosfstools, rsync, and GNU coreutils. Run the builder
as the ordinary user with working `sudo -n` for its loop-device operations. Never
run the builder itself as root. QEMU/KVM, OVMF and Pillow are also needed for the
boot check below. The recorded host provides these outside the tool sandbox;
missing sandbox `/dev/loop-control` or `/dev/kvm` does not establish they are
missing on the host.

The raw image's **logical length is 61,991,813,120 bytes** (57.73 GiB). It is sparse
on a supporting host filesystem; its allocated space is closer to the payload
size, but tools or copies can materialize all zero-filled regions. Reserve at
least the full logical size when uncertain. Preserve it with `cp --sparse=always`
when copying between suitable Linux filesystems. It cannot be stored as one
file on FAT32, although the filesystem inside the image is FAT32. Hashing the
whole image reads its complete logical length, including zeros in sparse holes.

## Bind fresh account tests to the complete candidate

For future builds, run this immediately after runbook step 4, **before starting
the account VMs**. It compares every file inside the candidate image with staging
and records `verification/candidate-payload-sha256.json`. This includes
`sources/setup.exe`, its other Setup resources, all boot files and all drivers.
The historical eight-file record alone did not cover all those files.

Run this Bash block from the isolated run root. The allocated loop device opens
the regular image read-only. It never names or opens a physical USB.

```bash
set -euo pipefail
candidate_image="$PWD/verification/test-usb.img"
candidate_mount="$PWD/verification/candidate-image-mount"
test -f "$candidate_image"
test ! -L "$candidate_image"
test ! -e verification/candidate-payload-sha256.json
mkdir "$candidate_mount"
candidate_loop=''
cleanup_candidate() {
  if mountpoint -q "$candidate_mount"; then sudo -n umount "$candidate_mount" || return; fi
  if test -n "$candidate_loop"; then sudo -n losetup -d "$candidate_loop"; fi
}
trap cleanup_candidate EXIT
candidate_loop=$(sudo -n losetup --find --show --partscan --read-only "$candidate_image")
sudo -n mount -o "ro,uid=$(id -u),gid=$(id -g),umask=022,nosuid,nodev,noexec" \
  "${candidate_loop}p1" "$candidate_mount"
CANDIDATE_MOUNT="$candidate_mount" python3 - <<'PY'
from pathlib import Path
import hashlib, json, os

def inventory(root):
    result = {}
    for p in sorted(root.rglob('*')):
        if p.is_symlink() or not (p.is_file() or p.is_dir()):
            raise SystemExit('Unsupported entry: '+str(p))
        if p.is_file():
            with p.open('rb') as f:
                result[p.relative_to(root).as_posix()] = hashlib.file_digest(f, 'sha256').hexdigest()
    return result

expected = inventory(Path('staging'))
actual = inventory(Path(os.environ['CANDIDATE_MOUNT']))
if not expected or expected != actual:
    raise SystemExit('Candidate image inventory or bytes differ from staging')
with Path('verification/candidate-payload-sha256.json').open('x') as f:
    json.dump(expected, f, indent=2)
    f.write('\n')
print('Verified complete candidate payload:', len(expected), 'files')
PY
cleanup_candidate
candidate_loop=''
trap - EXIT
rmdir "$candidate_mount"
```

Freeze that candidate throughout testing. After tests, add only the explicitly
reviewed documentation/evidence and final `SHA256SUMS.txt`. Before accepting the
final staging tree, run the following comparison. It refuses a change to any
file outside `Documentation/` and the checksum manifest. Every permitted change
is listed for review; it is not silently ignored. If other files must change,
repeat the affected tests and capture a new candidate snapshot.

```bash
set -euo pipefail
python3 - <<'PY'
from pathlib import Path
import hashlib, json
old = json.loads(Path('verification/candidate-payload-sha256.json').read_text())
new = {}
for p in sorted(Path('staging').rglob('*')):
    if p.is_symlink() or not (p.is_file() or p.is_dir()):
        raise SystemExit('Unsupported entry: '+str(p))
    if p.is_file():
        with p.open('rb') as f:
            new[p.relative_to('staging').as_posix()] = hashlib.file_digest(f, 'sha256').hexdigest()
changed = [n for n in sorted(old.keys() | new.keys()) if old.get(n) != new.get(n)]
functional = [n for n in changed if n != 'SHA256SUMS.txt' and not n.startswith('Documentation/')]
if not old or functional:
    raise SystemExit('Changed functional payload; repeat affected tests: '+repr(functional))
report = {'functional_payload_unchanged': True, 'documentation_or_manifest_changes': changed}
Path('verification/candidate-to-release-comparison.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
PY
```

Do not reconstruct a supposed pre-test snapshot from the final tree after the
tests. If it was not captured, disclose that missing evidence. The September 18
record retains its explicitly narrower historical hash/test scope.

## Create the release image

From the root containing the finalized staging tree:

```bash
set -euo pipefail
release_dir="$PWD/release/r1"
bash scripts/build-release-image.sh "$release_dir"
(cd "$release_dir" && sha256sum -c MSW11-Lenovo-x64.img.sha256)
```

Choose an unused release directory. The builder refuses an existing directory
and never overwrites a prior image. It verifies the ready record, the complete
staging file set, all payload hashes, the manifest itself, driver-manifest hash,
and recorded tested-file hashes before copying. After copying, it flushes and
detaches the writable loop, reopens the image read-only, checks partition/FAT
geometry, runs read-only filesystem checking, and verifies the entire image
payload again. Successful packaging publishes the final `.img`, its SHA-256
companion, and `release-image.json` with the inherited validation scope.

The output also retains command/check logs. Require successful builder exit and
the absence of `INCOMPLETE.txt`. A failed command, that marker, or a remaining
`.partial.img` is an incomplete package even if other final-looking files exist.
Inspect the error, ensure its loop and
mount are cleaned up, and use a new output directory after fixing the cause.
Never remove the partial marker just to make the file look finished.

The release builder's validation record consumes completed installation evidence;
it does not evaluate screenshots or run those installations. The image boot
check is a separate next step. Random partition IDs, filesystem IDs and build
timestamps can make two correct packages have different raw-image hashes; a
rebuild is not promised to be byte-for-byte reproducible.

FAT readback mounts need explicit `uid`, `gid` and `umask` options even when
read-only. The first integration run inherited a restrictive mask and its
ordinary-user verifier could not enumerate the root-owned remount. The builder
now sets readable ownership/masks on both mounts, and the verifier reports
directory-access errors explicitly instead of silently skipping those directories.

Partition size and FAT volume size are separate geometry fields. With the
builder's 255-head/63-sector track geometry, `mkfs.fat` aligns the FAT volume
down to **121,075,668 sectors**, leaving **44 sectors** at the end of the
121,075,712-sector partition. The checker requires this exact bounded rounding;
it does not accept an arbitrary smaller volume or an overrun. This behavior is
documented by `mkfs.fat -g` and implemented in the
[dosfstools 4.2 formatter](https://github.com/dosfstools/dosfstools/blob/v4.2/src/mkfs.fat.c#L733-L735).

## Boot the exact release image before handing it off

Use fresh disposable OVMF variables. This VM has no network and no installation
destination. Its only writable disk-like object is its private firmware-variable
file. Select a short, unused smoke directory, and use paths without commas (the
QEMU drive syntax below uses commas as separators).

```bash
set -euo pipefail
release_dir="$PWD/release/r1"
smoke_dir="$PWD/verification/r1"
image_path="$release_dir/MSW11-Lenovo-x64.img"
test -f "$image_path"
test ! -L "$image_path"
SMOKE_DIR="$smoke_dir" python3 - <<'PY'
from pathlib import Path
import os
p = Path(os.environ['SMOKE_DIR']).resolve()/'qmp.sock'
if len(os.fsencode(p)) > 107:
    raise SystemExit('Choose a shorter actual smoke directory')
PY
mkdir "$smoke_dir"
cp /usr/share/OVMF/OVMF_VARS_4M.ms.fd "$smoke_dir/vars.fd"
qemu-system-x86_64 -name MSW11-release-image-smoke \
  -enable-kvm -machine q35,smm=on -cpu host -smp 2 -m 4096 \
  -no-user-config -nodefaults -nic none -serial none -parallel none \
  -global driver=cfi.pflash01,property=secure,value=on \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.ms.fd \
  -drive "if=pflash,format=raw,file=$smoke_dir/vars.fd" \
  -drive "if=none,id=installer,format=raw,readonly=on,file=$image_path" \
  -device qemu-xhci,id=usb \
  -device usb-storage,drive=installer,removable=on,bootindex=1 \
  -device usb-kbd -device usb-tablet -vga std -boot strict=on \
  -display none -qmp "unix:$smoke_dir/qmp.sock,server=on,wait=off" \
  -pidfile "$smoke_dir/qemu.pid" -S -daemonize
/usr/bin/python3 scripts/qmp.py "$smoke_dir/qmp.sock" execute \
  '{"command":"query-named-block-nodes"}' > "$smoke_dir/block-graph-before-boot.txt"
```

The existing QMP helper prints Python-readable text, not JSON; keep the `.txt`
extension. Inspect the block graph **before resuming**: the release image and firmware code
must be read-only; only `vars.fd` may be writable; no other backing file may
appear. If any condition fails, stop the paused VM with `qmp.py ... quit` and
correct the launcher. Once the graph is confirmed:

```bash
set -euo pipefail
/usr/bin/python3 scripts/qmp.py "$smoke_dir/qmp.sock" execute '{"command":"cont"}'
# Allow the guest to progress, then take and inspect a screenshot.
/usr/bin/python3 scripts/qmp.py "$smoke_dir/qmp.sock" screenshot "$smoke_dir/menu.png"
```

Repeat the screenshot after observed progress until the actual local/Microsoft
account-choice menu is visible. A firmware logo does not pass this check. Save
the menu screenshot and graph, then select menu 4 to shut down:

```bash
set -euo pipefail
smoke_pid=$(cat "$smoke_dir/qemu.pid")
[[ "$smoke_pid" =~ ^[0-9]+$ ]]
/usr/bin/python3 scripts/qmp.py "$smoke_dir/qmp.sock" type $'4\n'
for attempt in {1..60}; do
  if ! test -S "$smoke_dir/qmp.sock" && ! kill -0 "$smoke_pid" 2>/dev/null; then break; fi
  sleep 1
done
test ! -S "$smoke_dir/qmp.sock"
if kill -0 "$smoke_pid" 2>/dev/null; then
  printf 'VM process has not exited; inspect it before continuing.\n' >&2
  exit 1
fi
(cd "$release_dir" && sha256sum -c MSW11-Lenovo-x64.img.sha256)
```

Record the image hash, firmware hashes, date, actual menu result and graph review
in a separate boot-test note, and retain the screenshot. Do not change the raw
image to add those late notes: keep them as external release evidence. The
builder's initial report correctly records that it did not perform this boot
check. A successful menu test supplements the preserved account-install tests;
it does not demonstrate Wi-Fi/Ethernet operation on physical Lenovo hardware.

## Hand off and flash the image

Deliver the raw `.img`, its `.img.sha256`, `release-image.json`, and the boot-test
evidence together. The image already contains an MBR, one active FAT32 partition,
Microsoft's UEFI loader, Setup and all finalized payload files. Write it to the
**whole USB device**, beginning at byte zero. Copying the `.img` onto an existing
USB filesystem, writing it to partition 1, or treating it as a Windows source ISO
will not reproduce this layout.

The recipient must check the drive's actual byte capacity is **at least
61,991,813,120** and its logical sector size is **512 bytes**. A marketed “64 GB”
label is insufficient; a smaller device cannot hold this image. A larger drive
leaves unused tail space. The installer uses UEFI boot; legacy BIOS boot is not
claimed. Consult the [Secure Boot guide](source-media-and-secure-boot.md) for the
2011/2023 trust and revocation limits.

The following Linux example is destructive and is **only for an explicitly
selected USB write job**. It is pinned to the original Kingston identity. For a
different USB, review and replace every identity value, retaining the capacity,
512-byte-sector and unmounted-child checks. Confirm that existing contents may
be erased before running it. These commands are documentation, not part of
building the image.

```bash
set -euo pipefail
release_dir="$PWD/release/r1"
image_path="$release_dir/MSW11-Lenovo-x64.img"
target=/dev/disk/by-id/usb-Kingston_DataTraveler_3.0_4CEDFB74A32C1A70790301C3-0:0
(cd "$release_dir" && sha256sum -c MSW11-Lenovo-x64.img.sha256)
python3 - "$target" "$image_path" <<'PY'
from pathlib import Path
import json, os, stat, subprocess, sys
target, image = sys.argv[1:]
if not stat.S_ISBLK(os.stat(target).st_mode):
    raise SystemExit('Target must be a whole USB block device')
nodes = json.loads(subprocess.check_output(['lsblk', '--tree', '-b', '-J', '-o',
    'PATH,SIZE,MODEL,SERIAL,TRAN,RM,TYPE,MOUNTPOINTS,LOG-SEC', target]))['blockdevices']
if len(nodes) != 1:
    raise SystemExit('Unexpected target topology')
d = nodes[0]
if not (d['type'] == 'disk' and d['tran'] == 'usb' and d['rm'] is True
        and d['serial'] == '4CEDFB74A32C1A70790301C3'
        and d['model'].strip() == 'DataTraveler 3.0'
        and int(d['log-sec']) == 512
        and d['size'] >= Path(image).stat().st_size
        and os.path.realpath(target) == d['path']):
    raise SystemExit('USB identity, capacity or sector size does not match')
def check_unmounted(node):
    if any(node.get('mountpoints') or []):
        raise SystemExit('Unmount the selected USB and its partitions first')
    for child in node.get('children', []):
        check_unmounted(child)
check_unmounted(d)
print('Reviewed write target:', d['path'], d['serial'], d['size'])
PY
# Remove old partition-table signatures, including a larger drive's backup GPT.
sudo -n wipefs --all "$target"
sudo -n dd if="$image_path" of="$target" bs=4M iflag=fullblock conv=fsync status=progress
sudo -n blockdev --flushbufs "$target"
sudo -n cmp --bytes="$(stat -c %s "$image_path")" "$image_path" "$target"
sudo -n blockdev --rereadpt "$target"
sudo -n udevadm settle
```

Require successful exit from both the write and comparison. The bounded `cmp`
compares every image byte and tolerates unused space only **after** the image on
a larger device. Prevent desktop automount during the write/readback; if it mounts
the finished partition afterward, unmount that selected partition before unplugging.
Record target identity, write/readback exit status and the image hash. A final
boot from the USB in the intended laptop's UEFI boot menu can confirm the account
menu; installation is a separate action. The runbook's physical-USB VM launcher
requires the three named readback/filesystem/partition logs from its direct-copy
workflow. This raw-flash example does not produce those logs, so that launcher
cannot simply be appended here or satisfied with an older job's evidence.

Do not use `conv=sparse` for the physical write: skipped zero blocks can retain
old device data. `conv=fsync` waits for output data/metadata to synchronize. These
options and their device behavior are described in the [GNU dd manual](https://www.gnu.org/s/coreutils/manual/html_node/dd-invocation.html);
the byte-limit behavior is in the [GNU cmp manual](https://www.gnu.org/software/diffutils/manual/html_node/cmp-Options.html).

Raw flashing writes the full 62 GB logical image, including its unused zero-filled
space. At the original drive's measured 8–10 MB/s, allow roughly **1.7–2.2 hours
for the write**, plus full readback. The earlier roughly 35-minute result used
the separate file-copy writer and must not be presented as a raw-image ETA.

Optional transport compression can reduce the file size: use `xz -T2 -1 -k`
on the completed image, retain the raw-image checksum, and produce a separate
checksum for the compressed file. Decompress and verify the raw image before
using the example above. Do not rename compressed bytes to `.img` or hash the
compressed stream and label it as the raw-image hash. Raw and compressed images
are ignored build products; keep reviewed recipes and compact evidence in Git.
