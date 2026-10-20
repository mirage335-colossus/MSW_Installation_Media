# Rebuild the preserved installer from a Git clone

This procedure preserves the **September 18, 2026 Windows 11 25H2 build** and
its E485/L14/L15/T15g driver selection. Use the exact frozen inputs and account
sources. It rebuilds installation media from Microsoft's ISO, not Windows from
source code. It does not update the Windows version or driver selection.

A clone contains the custom sources, frozen vendor metadata, hashes, procedures
and historical evidence. It intentionally excludes Microsoft's ISO and Lenovo's
binary payloads. For a future offline rebuild, retain **both the Git repository
and the verified binary-input cache** described below. URLs and hashes identify
inputs; they cannot recover files after a vendor removes them.

## Preserve the existing inputs

The smallest practical input cache uses the already extracted, complete driver
payload, so the original E485 installer archive need not be available again:

| Relative path under the cache root | Required content |
| --- | --- |
| `downloads/Win11_25H2_English_x64_v2.iso` | 8,471,603,200 bytes; SHA-256 `768984706b909479417b2368438909440f2967ff05c6a9195ed2667254e465e3` |
| `research-drivers/bootstrap-drivers/` | Exact preserved union: 171 directories at the package level, 5,166 files, 5,844,200,528 file bytes; includes both E485 chipset components and the final T15g additions |

Keep the **whole** driver directory tree, including CAT, SYS, DLL, firmware data,
extension and other package files; INFs alone are insufficient. Its expected file
set and every file hash come from the tracked `staging/SHA256SUMS.txt`, whose own
hash is bound by `verification/validation-ready.json`. The two inputs total about
14.32 GB of file data. Their metadata and provenance are already tracked in Git.

Run this from the checkout to check that cache without modifying it:

```bash
python3 -B scripts/check-clone-inputs.py --preserved --cache-root /path/to/cache
```

The existing workspace itself can be the cache root. Back up those two paths
outside the working disk, preserving their relative names and file contents.
Verify the copied cache with the same command; a successful check of the original
does not establish that its backup succeeded. Do not delete the only cache after
committing source changes. This procedure does not automatically create a backup.

Optionally preserve `research-drivers/packages/` with all **170 distinct source
installers**, plus an extracted cache, for replaying extraction itself. The
selected 169 installers and one E485 SCCM archive yield 171 staged package
directories because two components come from that shared archive. Check original
installers with `--downloads`; this is an alternative to `--preserved`, not a
requirement when rebuilding from the verified final driver payload.

Also retain the existing final `.img`, checksum and release report if the exact
previously built **image bytes** are needed. A fresh build can change WIM metadata
and filesystem IDs. Rebuilding the same inputs does not promise the old outer
image SHA-256. See [the image handoff bundle](ready-to-flash-image.md#hand-off-and-flash-the-image).

## Clone and check the source files

Use this repository's actual URL or a retained Git bundle; the commands do not
assume a public hosting service:

```bash
git clone <repository-url-or-bundle> msw11
cd msw11
python3 -B scripts/check-clone-inputs.py
```

The checker uses Python 3.11+ and Git, reads tracked paths, cross-checks the
frozen ISO identity, all 169 selected driver descriptors against their recorded
hashes, installer identities, the 170-entry checksum inventory, coverage counts
and account-profile restrictions. It makes no network requests, invokes no
`sudo`, writes no reports or caches, and does not attach or write disks.
`--json` prints a report to stdout for a caller to preserve.

**A source-input pass is not a build or boot pass.** With no binary cache present,
`--preserved` and `--downloads` should fail. Historical `staging/` and
`verification/` files in a clone must not be mistaken for a newly completed build.

## Prepare the Linux host

Use the [recorded host requirements](runbook.md#2-prepare-the-host-and-an-isolated-working-directory).
For Debian 13, the corresponding package installation is:

```bash
sudo apt-get update
sudo apt-get install git bash python3 python3-pil python3-requests \
  7zip wimtools innoextract cabextract dosfstools mtools fdisk util-linux \
  rsync coreutils qemu-system-x86 qemu-utils ovmf swtpm openssl xorriso curl sudo
python3 -B scripts/check-clone-inputs.py --host
```

Use the distribution's package equivalents elsewhere. The scripts call `7z`;
Debian's [7zip file list](https://packages.debian.org/trixie/amd64/7zip/filelist)
includes that command, while `7zip-standalone` supplies `7zz`. The host check
examines the required commands, firmware paths, Pillow, visible KVM/loop devices
and the default run path's socket length. It does not prove sudo authorization,
open a device, install packages or test firmware trust. Resolve any reported
environment limitation before the relevant build/VM step; run it on the actual
build host if a restricted shell hides devices.

Reserve the runbook's 110–130 GiB workspace estimate, more if retaining additional
images or making nonsparse copies. Use a short actual path, fresh VM disks and
private OVMF/TPM state. Do not enable `PYTHONOPTIMIZE` or run Python with `-O`.

## Restore the frozen cache and initialize a new run

First restore the verified ISO and driver payload into the clone's ignored cache
locations. These commands fail if those destinations already exist:

```bash
set -euo pipefail
cache_root=/path/to/retained/cache
test ! -e downloads/Win11_25H2_English_x64_v2.iso
test ! -e research-drivers/bootstrap-drivers
cp --reflink=auto "$cache_root/downloads/Win11_25H2_English_x64_v2.iso" downloads/
cp -a --reflink=auto "$cache_root/research-drivers/bootstrap-drivers" research-drivers/
python3 -B scripts/check-clone-inputs.py --preserved
```

Now follow **runbook step 2**, starting in this checkout. Its first shell block
creates a fresh `.runs/a` (or another short, unused label), copies the custom
sources and frozen driver metadata/cache, and creates **empty** staging and
verification directories. Its ISO-copy block copies the verified ISO and
provenance, then changes into that new run root. Do not copy the historical
`staging/Documentation/Validation` or `verification/validation-ready.json` into
the new run.

For this preserved-payload route, do **not** run `stage_bootstrap.py`: it consumes
the extracted source cache, which this route does not require. Run
`validate_payload.py` as directed by runbook step 3, then assemble/cross-check
the existing driver payload and documentation using that step's Python block.
The new driver-copy comparison and subsequent tests belong to this new run.

If the preserved cache is unavailable, the
[frozen driver replay](driver-maintenance.md#reproduce-the-frozen-driver-collection)
can recover missing original installers from their recorded Lenovo URLs and
verify them before extraction. It creates a separate `run_dir`; copy its verified
payload and regenerated reports into `run_root/research-drivers` before assembly.
The ISO must still match the frozen identity above. A renamed or newer ISO is not
a replacement. The original Microsoft download link has expired; the
[acquisition record](source-media-and-secure-boot.md#acquisition-lessons) explains
how it was obtained. A new link is useful only if it supplies those exact bytes.
If a required original input cannot be recovered, record that as a missing
dependency rather than changing the reference build.

## Build and test the new media

Continue the existing procedures in this order, from the isolated run root:

| Stage | Procedure and exit condition |
| --- | --- |
| Prepare and assemble | [Runbook step 3](runbook.md#3-verify-inputs-and-assemble-the-complete-candidate): verify the pinned ISO; customize boot WIM index 2; split the install WIM; copy the complete drivers and docs; hash every copied driver file |
| Candidate | [Runbook step 4](runbook.md#4-build-and-bind-the-test-image): build a regular test image and capture the complete pre-test snapshot/readback |
| Installation tests | [Runbook step 5](runbook.md#5-perform-the-vm-and-driver-tests): fresh Home/local offline desktop, fresh Pro/Microsoft online sign-in form, driver acceptance and independent installed-disk boot |
| Finalization | [Runbook step 6](runbook.md#6-finalize-only-real-completed-evidence): review new evidence; bind it to the tested bytes; finalize the payload manifest |
| Ready-to-flash image | [Runbook step 7](runbook.md#7-produce-and-verify-the-ready-to-flash-image): package a new `.img`, verify its readback/geometry/filesystem, boot the exact image read-only and recheck its SHA-256 |

The final command, after those gates, is:

```bash
bash scripts/build-release-image.sh "$PWD/release/r1"
```

Use the [acceptance guide and report template](testing-and-acceptance.md) to record
what passed. The online account service can behave differently even with frozen
media; preserve new observations without rewriting the September evidence.
Hardware tests remain separate from VM driver acceptance. A clone check does not
extend coverage to untested Lenovo adapters or firmware.

Building the image requires no USB write. Follow the separate, identity-checked
flashing procedure only when a physical target is deliberately selected.

## Verify that a future commit remains sufficient

From a **different local clone of the commit**, with ignored caches absent:

```bash
python3 -B scripts/check-clone-inputs.py --json
python3 -B -m unittest discover -s tests -v
python3 -B scripts/check-clone-inputs.py --preserved --cache-root /path/to/retained/cache --json
```

This checks that the required sources are actually tracked and that the retained
binary inputs match the reference inventory. Perform the full build and acceptance
workflow when claiming a newly rebuilt image works. Keep source audit, cache
verification, new build tests and inherited evidence distinct.
