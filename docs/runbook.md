# Rebuild, test, and write the installation media

For a clone with no ignored binary inputs, start with
[restoring the preserved build](from-git-clone.md). It distinguishes the verified
final driver-cache route from replaying the original installer extraction.

This is the maintainer procedure for the **2026-09-18 reference build**. Read the
[lessons](lessons-learned.md) before running it. The commands below are a recipe
for a new run, not a request to rewrite a connected disk merely to update docs.
Use [testing and acceptance](testing-and-acceptance.md) to choose required endpoints,
assess errors and complete a fresh test report before claiming an image or USB is usable.

The intended result is a UEFI installer that explicitly offers either an
interactive local account or Microsoft sign-in, with factory-variant bootstrap
drivers for E485, L14/L15, and T15g Gen 1. It must reach installation and a usable
desktop/network starting point without embedding credentials, choosing the
destination disk, or configuring automatic partition deletion. Optional graphics
acceleration and other features can follow through Windows/Lenovo updates.

## 1. Choose a rebuild or a refresh

| Operation | Required work |
| --- | --- |
| Write another copy of the **identical verified payload** | Check its complete file set/hashes, confirm the new physical target, write, flush, read back and boot that USB. Preserve the original test scope. No claim of newly verified online OOBE behavior. |
| Produce a **ready-to-flash image file** | Complete staging and finalization, package it into a fresh whole-device `.img`, verify its complete payload and geometry, boot it read-only, and retain the outer image checksum and report. No connected USB is required. |
| Rebuild the same ISO and driver snapshot | Recover the ignored inputs, assemble in a fresh directory, and test the resulting files. WIM repacking may change bytes; do not assume historical hashes still apply. |
| Change the ISO, account profile, launcher, drivers or supported machine types | Refresh the relevant research, build, perform fresh tests, and bind their evidence to the new hashes. Treat new online OOBE behavior as unstable even when a report is only days old. |

For new account claims, revisit the current Microsoft page and the primary
upstream/community evidence linked in [the account guide](account-choice-and-testing.md).
Record access dates, release/commit versions, ISO hash and actual build numbers.
A source's publication date is useful context; observed behavior of the exact
image is the stronger test. The September 18 snapshot does not prove later
Microsoft service behavior.

For driver refreshes, use [driver maintenance](driver-maintenance.md). The old
scripts are useful building blocks, not a complete all-model live updater.
Do not use the host laptop's NIC inventory as the supported-model inventory.

## 2. Prepare the host and an isolated working directory

The reference host was Debian x86-64 Linux with Python 3.13.5, Pillow 11.1.0,
requests 2.32.3, KVM, OVMF, and swtpm. `hashlib.file_digest` requires Python 3.11+
and QMP screenshots require Pillow. The observed Debian package mapping was:

```text
7zip, wimtools, dosfstools, mtools, fdisk, util-linux, rsync,
qemu-system-x86, qemu-utils, ovmf, swtpm,
innoextract, cabextract, openssl, xorriso,
python3, python3-pil, python3-requests
shellcheck (optional static checking)
```

Check the actual distribution's package names before installing missing tools.
The scripts expect `7z`, `/usr/sbin/sfdisk`, `mkfs.vfat`, and
`/usr/share/OVMF/OVMF_{CODE,VARS}_4M.ms.fd`; do not silently substitute a firmware
template with a different size or trust configuration. Verify `/dev/kvm` access
and sudo access for loop mounts and the eventual physical-device operations.
Run normal build scripts as the ordinary user; they invoke `sudo -n` for their
privileged operations. Never run Python with `-O` or set `PYTHONOPTIMIZE`: existing
guards use assertions.

Each reference VM used four vCPUs and 6 GiB RAM. Run them sequentially if there
is insufficient headroom for two plus the host. Budget roughly **110–130 GiB of
free workspace** for a full fresh copy, source/extracted drivers, staging, a test
USB image and both installed VMs. Sparse logical capacity is not allocated disk
space, but it grows during installation. The first run ultimately reclaimed
70.36 GiB by deleting only its disposable VM/test disks after exporting evidence.

Do not overwrite this repository's historical `verification/` or use its old
pass files as inputs to a new test. An isolated run also avoids the writers'
fixed-relative-output paths and the smoke launcher's refusal to reuse a directory:

```bash
set -euo pipefail
# Start in the repository root. Use a short, unused run label.
repo_root=$PWD
run_label=a
run_root="$repo_root/.runs/$run_label"
RUN_ROOT="$run_root" python3 - <<'PY'
import os
from pathlib import Path
root = Path(os.environ['RUN_ROOT']).resolve()
for suffix in ['verification/local/tpm.sock', 'verification/cloud/qmp.sock',
               'verification/physical-boot/qmp.sock',
               'verification/t15g-windows-validation/tpm.sock']:
    path = root/suffix
    if len(os.fsencode(path)) > 107:
        raise SystemExit('Unix socket path too long; choose a shorter actual run root: '+str(path))
PY
mkdir -p "$repo_root/.runs"
mkdir "$run_root"                 # deliberately fails if it already exists
cp -a scripts research-accounts docs README.md "$run_root/"
mkdir "$run_root/downloads" "$run_root/staging" "$run_root/verification"
cp -a --reflink=auto research-drivers "$run_root/"
cp staging/README.txt "$run_root/INSTALL-README.txt"
cp verification/secureboot/README.md "$run_root/SECURE-BOOT-NOTES.md"
```

Linux Unix-domain socket names are limited in bytes. With this repository's
long absolute path, `.runs/a` fits even the longer T15g test path; a descriptive
date label does not. Record the date/purpose in the run notes instead. On another
host, choose a shorter **actual** directory on a filesystem with enough space if
the check fails. A short symlink is insufficient when scripts resolve real
paths. Do not assume `/tmp` has enough disk capacity or survives a reboot.

The driver copy contains cached binaries only when they exist locally. A fresh
Git clone excludes them: restore/download them using the driver guide. If that
guide creates a separate replay directory, bring its verified `bootstrap-drivers/`
tree and regenerated manifests/coverage/check reports into this run's
`research-drivers/`, retaining the copied frozen source metadata. Do not confuse
the standalone replay's `run_dir` variable with this procedure's `run_root`.
The maintainer guides link historical evidence in the original checkout; read
those links there rather than populating this run's fresh verification directory
with old pass artifacts. `cp --reflink=auto` makes an independent copy when
supported and otherwise consumes
real space. Do not hard-link files that later extraction/build steps may modify.

Copy a cached ISO into the new run, or acquire it through the official flow:

```bash
set -euo pipefail
cp --reflink=auto downloads/Win11_25H2_English_x64_v2.iso "$run_root/downloads/"
cp downloads/windows11-iso-provenance.json "$run_root/downloads/"
cp downloads/Win11_25H2_English_x64_v2.iso.sha256 "$run_root/downloads/"
cd "$run_root"
```

The command intentionally fails if the ignored ISO is absent. Follow
[source acquisition](source-media-and-secure-boot.md) instead of inventing a
download URL. Review/update `INSTALL-README.txt` and the provenance for a changed
release, and review `SECURE-BOOT-NOTES.md` against the intended firmware trust
conditions. Future runs inside `.runs/` are ignored; retain selected new source
changes and reviewed evidence in Git only when deliberately promoting a result.

## 3. Verify inputs and assemble the complete candidate

`scripts/prepare-media.py` pins the original ISO filename and published SHA-256.
For another release, update both from independently checked official provenance
in the isolated run and review edition/image indices before using the script.
It modifies **boot.wim index 2**, copies the account profiles/helper, checks for
unwanted unattended actions, splits install.wim at 3800 MiB, and verifies WIM
resources. It does **not** collect/copy the driver union or documentation.

```bash
set -euo pipefail
python3 scripts/prepare-media.py
python3 research-drivers/validate_payload.py
```

Use `--resume` only after inspecting a partial failure and confirming that the
original `staging/sources/install.wim` still exists. A successful run deletes that
file after split verification, so `--resume` is not a second-run shortcut. Start
again in a fresh workspace for a completed candidate. Preserve useful failure
logs separately before a retry overwrites them.

Assemble the final driver union before account testing. The following copies
the already verified cache, its provenance and docs, then hashes **every source
and destination file** and checks the exact relative-path sets:

```python
# Run from the isolated run root: python3 - <<'PY' ... PY
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil

source = Path('research-drivers/bootstrap-drivers')
dest = Path('staging/$WinPEDriver$')
if not source.is_dir() or dest.exists():
    raise SystemExit('Need a verified source and a fresh destination')
shutil.copytree(source, dest)
docs = Path('staging/Documentation')
docs.mkdir()
(docs/'SecureBoot').mkdir()
secure_boot_notes = Path('SECURE-BOOT-NOTES.md').read_text()
secure_boot_notes = secure_boot_notes.replace(
    'Raw PKCS7, readable certificates, file hashes, and dates are in this directory and `certificates-summary.json`.',
    'The historical raw PKCS7, readable certificates, file hashes and dates are retained '
    'under `verification/secureboot/` in the source repository, including '
    '`certificates-summary.json`. They are not shipped beside this USB README.')
secure_boot_notes = secure_boot_notes.replace(
    'Read-only extraction from install.wim image 1 produced:',
    'The September 18 inspection extracted the following files from install.wim image 1 '
    'for analysis. These paths describe that inspection; the extracted EFI binaries '
    'are not shipped in this documentation directory:')
(docs/'SecureBoot/README.md').write_text(secure_boot_notes)
for p in Path('research-drivers').iterdir():
    if p.is_file() and p.suffix in {'.json', '.tsv', '.sha256', '.txt', '.xml', '.log'}:
        shutil.copy2(p, docs/p.name)
shutil.copytree('research-drivers/metadata', docs/'Lenovo-source-metadata')
driver_readme = Path('research-drivers/README.md').read_text()
(docs/'DRIVERS.md').write_text(driver_readme.replace('`bootstrap-drivers/`',
    '`$WinPEDriver$/`').replace('`metadata/`', '`Lenovo-source-metadata/`'))
shutil.copy2('research-accounts/README.md', docs/'ACCOUNT-RESEARCH.md')
shutil.copy2('downloads/windows11-iso-provenance.json', docs/'windows11-iso-provenance.json')
shutil.copy2('INSTALL-README.txt', 'staging/README.txt')

def inventory(root):
    result = {}
    for p in sorted(root.rglob('*')):
        if p.is_symlink():
            raise SystemExit('Unexpected symlink: '+str(p))
        if p.is_file():
            with p.open('rb') as f:
                result[p.relative_to(root).as_posix()] = hashlib.file_digest(f, 'sha256').hexdigest()
    return result

a, b = inventory(source), inventory(dest)
if not a or a != b:
    raise SystemExit('Driver source/staging paths or contents differ')
report = {
    'checked_at_utc': datetime.now(timezone.utc).isoformat(),
    'source': str(source), 'staged': str(dest),
    'files_compared': len(a), 'all_file_sha256_equal': True,
    'bytes_compared': sum(p.stat().st_size for p in source.rglob('*') if p.is_file()),
    'mismatches': [], 'extra_staged_files': [],
}
Path('verification/final-driver-staging-validation.json').write_text(json.dumps(report, indent=2)+'\n')
Path('verification/driver-file-sha256.json').write_text(json.dumps(a, indent=2)+'\n')
print(report)
```

Review the copied research dates and model maps. Label any preserved old research
as historical; don't claim its earlier VM results apply to the new candidate.
Include reviewed Secure Boot notes and up-to-date use instructions in
`staging/Documentation`. Keep fresh test evidence in a new `Documentation/Validation`
directory. Do not copy the old validation-ready file, final report, old screenshots
or old account-tested hashes into those evidence locations.

Before building the test image, confirm: no root `autounattend.xml`, no credential
or disk-target elements, exactly the intended account menu/profiles, no file at
or above 4 GiB, complete catalogs and driver source hashes, correct machine-type
coverage, and enough FAT32 allocated space. See the specialized guides for
the checks, rather than changing a failing guard merely to continue.

## 4. Build and bind the test image

```bash
set -euo pipefail
bash scripts/build-test-media.sh
```

This creates a **regular sparse file**, `verification/test-usb.img`, using the
same 61,991,813,120-byte capacity, MBR active type-c partition at sector 2048,
FAT32 and 32 KiB clusters as the original USB. It mounts only its allocated loop
device and refuses an existing image. For another USB geometry, update this
builder and the physical writer together and retest.

Capture the critical candidate hashes **before** tests, and verify the files
inside the actual test image match staging. This example streams large files
instead of loading a multi-gigabyte WIM into Python memory:

```python
from pathlib import Path
import hashlib, json, subprocess

names = ['sources/boot.wim', 'sources/install.swm', 'sources/install2.swm',
         'sources/install3.swm', 'efi/boot/bootx64.efi', 'profiles/local.xml',
         'profiles/microsoft.xml', 'MSW11-MEDIA.ID']
result = {}
for name in names:
    with (Path('staging')/name).open('rb') as f:
        expected = hashlib.file_digest(f, 'sha256').hexdigest()
    h = hashlib.sha256()
    with subprocess.Popen(['mtype', '-i', 'verification/test-usb.img@@1048576',
                           '::/'+name], stdout=subprocess.PIPE) as p:
        while chunk := p.stdout.read(1024*1024):
            h.update(chunk)
        if p.wait() != 0 or h.hexdigest() != expected:
            raise SystemExit('Test media mismatch: '+name)
    result[name] = expected
Path('verification/candidate-tested-file-sha256.json').write_text(json.dumps(result, indent=2)+'\n')
```

Adjust the split-file list if a refreshed ISO produces a different number of
parts. Before starting account tests, also perform the
[complete candidate readback and snapshot](ready-to-flash-image.md#bind-fresh-account-tests-to-the-complete-candidate).
It saves `verification/candidate-payload-sha256.json` for every file, including
the launched `sources/setup.exe`, other Setup resources and all driver files.
These eight historical hashes alone do not describe every file. Freeze the
candidate during testing and retain its source ISO/provenance and driver manifests.

## 5. Perform the VM and driver tests

Follow the [account test procedure](account-choice-and-testing.md), including
fresh disk/OVMF/TPM initialization, UI interaction, evidence export and shutdown.
The existing launcher does not create those initial files. Both reference paths
must pass: **Home/local offline through desktop** and **Pro/Microsoft online
through an empty sign-in form**. Never supply real cloud credentials just to
check that the sign-in option exists. State the endpoint honestly in the report.

Normally include the entire final driver union in both installs. The original
run's T15g addition occurred later; its separate
[Windows acceptance procedure](driver-maintenance.md) verified all new inputs
without claiming a complete second installation on actual T15g hardware.
If changing drivers alone, record what was rechecked and what unchanged prior
image/profile tests are being reused. Any changed boot/profile/ISO bytes require
new account-flow testing.

Export setup/PnPUtil logs and inventories before shutting down. Check the actual
local user's `PrincipalSource`, independent internal-disk boot, and Secure Boot
state. Distinguish duplicate INF paths from unique hashes and actual imported
driver-store entries. Review new warnings/errors in context. Finally record
hardware tests separately: exact model/type, BIOS/storage mode, network hardware
IDs, disk visibility, basic display/desktop, Wi-Fi association and internet,
Ethernet link and internet, and any manual driver recovery used.

## 6. Finalize only real, completed evidence

`finalize-media.py` **does not run tests or read screenshots**. It checks the
presence of expected files, compares the stored eight hashes, requires the
snapshot driver-file count of 5,166, hashes staging, and emits a pass record.
Its assumptions make operator review essential. An old PNG plus an old report
is not a test. Keep evidence from this run, with actual outcomes and limits.

After both account endpoints have been observed, copy this run's screenshots
to the filenames the finalizer expects:

```text
staging/Documentation/Validation/local-home-desktop.png
staging/Documentation/Validation/local-account-secureboot.png
staging/Documentation/Validation/cloud-microsoft-signin.png
staging/Documentation/Validation/cloud-test-notes.md
```

Include local test notes, source/driver checks and an explicit result table as
well. Promote `candidate-tested-file-sha256.json` to
`verification/account-tested-file-sha256.json` only after those tests pass and
the candidate is still unchanged. Update finalizer assumptions deliberately for
new verified counts or split parts; retain checks with the new measured values.

```bash
set -euo pipefail
cp verification/candidate-tested-file-sha256.json verification/account-tested-file-sha256.json
python3 scripts/finalize-media.py
```

For a fresh run, perform the candidate-to-release comparison in the image guide
and review its explicit list of documentation/manifest changes. Functional
payload changes require affected tests to repeat. The September 18 record did
not contain that complete pre-test snapshot; preserve its narrower dated scope.

Freeze **all** staged content after finalization. `sha256sum -c` checks listed
files but does not find unlisted additions: any addition, deletion or edit
requires regeneration of the manifest and review of whether tests must repeat.
Do not fabricate or manually flip `account_validation` to bypass a failed test.

## 7. Produce and verify the ready-to-flash image

Follow [release image creation](ready-to-flash-image.md) to run
`bash scripts/build-release-image.sh "$PWD/release/r1"`, verify the final `.img`
and checksum/report, and boot that exact image read-only to the account menu.
The release builder creates a new image **after** finalization. The earlier
`verification/test-usb.img` remains a candidate and must not be relabeled as the
release image. Its contents predate the final evidence and checksum manifest.

This is a complete endpoint when the requested deliverable is an image for a
USB flasher: hand off the `.img`, `.img.sha256`, release report and boot evidence.
No physical USB write is required to complete image creation. Record the inherited
account/driver test scope and packaging date separately.

## 8. Optionally select the physical target, write, and verify

For a byte-for-byte flash of the ready image, use the whole-device procedure in
the [image guide](ready-to-flash-image.md#hand-off-and-flash-the-image). The
existing commands below are the alternative **direct staging-to-USB file-copy**
workflow from September 18. `write-verified-usb.sh` does not consume a `.img`, and
its newly generated partition/filesystem IDs need not match the raw image hash.

This stage erases the selected USB. Confirm the intended drive's contents,
identity and authorization for the current job. Never infer the target from a
drive letter or `/dev/sda` alone. The reference writer is deliberately pinned to:

```text
/dev/disk/by-id/usb-Kingston_DataTraveler_3.0_4CEDFB74A32C1A70790301C3-0:0
model: DataTraveler 3.0
serial: 4CEDFB74A32C1A70790301C3
size: 61,991,813,120 bytes; transport: usb; removable: true
```

Inspect with `lsblk --tree -b -J -o
PATH,SIZE,MODEL,SERIAL,TRAN,RM,TYPE,MOUNTPOINTS`. Use `--tree`: without it the
original command flattened disk and partition entries. For a different physical
USB, review every target/capacity guard in **both** `write-verified-usb.sh` and
`start-physical-usb-test.sh`, plus the test-image geometry. Keep exact identity
and unmounted-child checks; do not weaken them into an arbitrary device argument.

Only after target review and all release gates:

```bash
set -euo pipefail
bash scripts/write-verified-usb.sh > verification/usb-write.log 2>&1
```

The script verifies staging, formats, copies, calls `sync -f`, unmounts, flushes
the block buffers, remounts read-only, checks payload hashes, unmounts again,
runs `fsck.vfat -n`, and records the partition table. Require successful exit and
the explicit completion line. Check that readback contains the **expected full
count** of `: OK` lines and no mismatches, not merely a few successful lines.

Also verify the physical checksum manifest itself, as the original final check
did (substitute a newly reviewed target only if appropriate):

```python
from pathlib import Path
import hashlib, json, subprocess
target = '/dev/disk/by-id/usb-Kingston_DataTraveler_3.0_4CEDFB74A32C1A70790301C3-0:0-part1'
ready = json.loads(Path('verification/validation-ready.json').read_text())
b = subprocess.check_output(['sudo', '-n', 'mtype', '-i', target, '::SHA256SUMS.txt'])
if hashlib.sha256(b).hexdigest() != ready['sha256_manifest_sha256']:
    raise SystemExit('Physical checksum manifest differs')
```

Expect USB write/flush to be much slower than RAM-buffered copy progress. The
observed drive committed roughly 8–10 MB/s while rsync sometimes displayed much
higher rates or 100%. Do not disconnect at 100%; wait for the flush/readback.
Read progress logs with `read_text().splitlines()` because they use carriage
returns. Prefer milestones and committed/readback progress to unstable ETAs.

## 9. Boot the physical USB read-only and close the run

```bash
set -euo pipefail
sudo -n bash scripts/start-physical-usb-test.sh
sudo -n python3 scripts/qmp.py verification/physical-boot/qmp.sock screenshot verification/physical-usb-menu.png
```

Wait for the account menu and inspect the screenshot. A boot logo alone is not
a pass. The launcher checks the exact target and both read-only block layers
before starting the VM CPUs; its allowed storage is the USB and disposable
firmware state only. No network, host internal disk or installation destination
is attached. It refuses an existing `verification/physical-boot` directory—use
a fresh run or archive completed evidence instead of overwriting variables.

Select menu **4** to shut down the test VM. Confirm its socket/process has ended
and that the USB/children are unmounted before declaring it ready. Preserve
the block-graph proof, menu screenshot, filesystem and readback results, source
and final hashes, actual test scopes, target identity and completion timestamp.
Root-owned smoke-test artifacts may need ownership restored after the VM stops
so the maintainer can inspect them.

Only then delete specifically named disposable VM/test disk files, after logs
and screenshots are exported and all their VMs have shut down. Never recursively
clean a mount point or use a wildcard across `verification/`—it can contain an
actual mounted USB. Keep the source ISO/cache when useful for another build;
keep binaries and mutable TPM/VM state out of Git.

Write a concise new completion report. Include real hardware limits, E485's
unsupported CPU/Windows 10 driver status, the actual cloud test endpoint, and
Secure Boot firmware trust limits. Record changed sources and lessons. Promote
only reviewed recipes/provenance/evidence from the ignored run directory back
into the repository, under a dated location rather than relabeling the 2026-09-18
results as a new success.
