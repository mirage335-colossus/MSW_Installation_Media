# Ready-to-flash image packaging validation — September 19, 2026

The documented release-image procedure was exercised against the **unchanged,
finalized September 18 installer payload**. The third integration run completed
successfully and the finished image booted read-only to the account-choice menu.
No physical USB was written during these packaging tests.

| Result | Evidence |
| --- | --- |
| Complete image, 61,991,813,120 logical bytes | [Release report](r3/release-image.json), [checksum](r3/MSW11-Lenovo-x64.img.sha256) |
| All 6,633 payload files plus `SHA256SUMS.txt` matched; 623 non-root directories matched | [Source verification](r3/source-preflight.json), [read-only image readback](r3/readback-verification.json) |
| 14,276,211,222 file bytes including the manifest | Same source/readback reports; raw filesystem overhead and unused space are separate |
| Exact MBR/FAT32 layout, 512-byte sectors, 32 KiB clusters | [Geometry](r3/geometry-verification.json), [filesystem check](r3/filesystem-check.log) |
| Actual local/Microsoft account-choice menu visible | [Menu screenshot](boot/menu.png) |
| Installer read-only at both raw and file layers; only private firmware variables writable | [Block graph](boot/block-graph-before-boot.txt), [preboot review and firmware hashes](boot/preboot-verification.json) |
| Menu option 4 shut down the guest; whole-image checksum still matched | [Shutdown and checksum result](boot/shutdown-and-final-checksum.log) |
| Source/tool identity retained | [Script hashes](build-tools.sha256), [tool versions](tool-versions.txt), [ISO provenance](source-iso-provenance.json) |

The successful local artifact is `release/r3/MSW11-Lenovo-x64.img`. Its SHA-256 is:

```text
0647f68a9151511f9fa9b74b9f8d62267efacb55712da6852da9c640e2d5ef37
```

It occupied 14,323,875,840 allocated bytes on the observed sparse-capable host
filesystem. The complete logical image is still about 62 GB and raw flashing
writes that full length. The image and local packaging outputs are ignored by
Git; the compact evidence in this directory is retained. A clone must rebuild
the image using the [image guide](../../docs/ready-to-flash-image.md).

## Actual scope

[RESULT.json](RESULT.json) records the completed packaging and boot checks.
The builder's own `boot_smoke_test_performed: false` remains accurate: the boot
test was performed afterward, with the exact command blocks saved as
[launch-from-guide.sh](boot/launch-from-guide.sh) and
[shutdown-from-guide.sh](boot/shutdown-from-guide.sh). Those are recorded commands
from this run, not reset/reuse helpers; choose fresh paths using the guide.

Packaging consumed the dated installation evidence identified by
[source-validation-ready.json](r3/source-validation-ready.json). It did **not**
rerun Home/local or Pro/Microsoft installation, authenticate a Microsoft account,
or test Wi-Fi, Ethernet, storage or other devices on physical Lenovo laptops.
The earlier Home/offline local-desktop and Pro/online empty-sign-in-form endpoints
remain their exact claimed scope. The original full account installs used the
159-package baseline, followed by the separate T15g acceptance test. The final
171-package union is included in this image.

The historical account evidence had eight selected file hashes, not the full
pre-test candidate snapshot now required by the guide for fresh builds. No
retrospective candidate snapshot was invented. The source payload manifest and
all-file readback establish which finalized bytes this image contains.

## Failures found while testing the documented workflow

1. **r1 — unreadable readback mount.** Formatting/copying succeeded, but the
   root-owned read-only FAT mount inherited restrictive access permissions.
   The ordinary-user verifier could not enumerate its contents. It failed with
   a missing-file inventory and did not publish an image. The fix sets explicit
   user/group/mask options on both mounts and makes `os.walk` report enumeration
   errors rather than silently skipping inaccessible directories.
   [Build log](r1/build.log), [incomplete marker](r1/INCOMPLETE.txt).
2. **r2 — overly strict volume-size equality.** All files matched and
   `fsck.vfat -n` passed. The geometry check then rejected the FAT volume's
   legitimate whole-track rounding. With 63 sectors per track, the formatter
   uses 121,075,668 volume sectors inside the 121,075,712-sector partition,
   leaving 44 sectors (22,528 bytes). The builder now pins 255/63 geometry and
   the verifier requires exactly that result, continuing to reject smaller
   volumes, overruns or other deviations.
   [Build log](r2/build.log), [observed geometry](r2/observed-geometry.json),
   [filesystem check](r2/filesystem-check.log).
3. **r3 — complete pass.** A fresh build exercised both fixes, complete payload
   readback, geometry/filesystem validation, whole-image hashing, the actual
   read-only boot menu, guest shutdown and an independent GNU SHA-256 check.
   [Build log](r3/build.log), [completed result](RESULT.json).

Static checks included ShellCheck, Bash syntax and Python compilation. During
development, 23 bounded helper cases exercised valid inputs and malformed or
changed payloads (hashes, inventories, names, special files, evidence and geometry).
After the integration failures, the unreadable-directory regression and 11 focused
geometry checks were exercised, including the real r2 header and incorrect sector
counts/track geometry. These were inline development checks, not a retained
standalone test suite. The final full integration above is the release proof.

The failed images and disposable firmware state were deleted only after copying
their evidence and successfully testing r3. No loop devices or mounts remained.
[Cleanup record](cleanup.json). The verified r3 image was retained.

## Repeat the work

Use the [runbook](../../docs/runbook.md) for a fresh ISO/driver/account build,
then the [image guide](../../docs/ready-to-flash-image.md) for packaging and testing.
For another package of the identical finalized payload, from the run root:

```bash
set -euo pipefail
bash scripts/build-release-image.sh "$PWD/release/r4"
```

Choose a new output directory if that example exists. Require successful exit,
no `INCOMPLETE.txt`, an image/checksum/report, the full readback and geometry
checks, and a fresh read-only image boot. Retain the new evidence under a new
dated location instead of overwriting this directory. Account or functional
payload changes require the affected installation tests to repeat.
