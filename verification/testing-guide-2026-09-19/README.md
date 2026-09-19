# Standalone image-verification recipe check — September 19, 2026

The first two Bash blocks in [Testing and acceptance](../../docs/testing-and-acceptance.md#record-the-artifact-and-environment-before-testing)
were extracted unchanged into [recheck-from-guide.sh](recheck-from-guide.sh) and
executed from the repository root against the existing `release/r3` image. The
complete script exited **0**. Its temporary output directory was `verification/t1`;
the resulting evidence was moved here after successful verification and cleanup.
Paths in the original reports deliberately retain that execution location.

| Newly performed check | Result and evidence |
| --- | --- |
| Reference bundle, declared length, absence of incomplete packaging markers | PASS; initial script check and successful execution |
| Complete image SHA-256 | PASS; [GNU checksum result](image-sha256.txt) |
| MBR/FAT32 geometry | PASS; [geometry report](geometry.json) |
| Correct backing file and read-only loop attachment | PASS; [loop metadata](loop-read.json), verifier exited 0 |
| Unmounted, read-only FAT check | PASS; [filesystem output](filesystem-check.txt), exit 0 |
| Exact file inventory, all hashes, manifest itself and directory layout | PASS; [payload report](payload-readback.json), [summary](payload-readback.txt) |
| Mount and loop cleanup | PASS; [cleanup record](cleanup.txt) |

The image has **61,991,813,120 bytes**, SHA-256
`0647f68a9151511f9fa9b74b9f8d62267efacb55712da6852da9c640e2d5ef37`.
The payload check matched **6,634 files including the manifest**, totalling
14,276,211,222 bytes, and 623 non-root directories. The filesystem tool's count
of 7,258 includes directory entries; it is not the payload file count.

The check ran on September 19, 2026, in the `America/Chicago` timezone; report
files were completed at 09:18:39–09:18:59 CDT. [Result metadata](RESULT.json)
records the tested artifact, execution result and scope. [Tool hashes](tools.sha256)
identify the executed recipe and payload verifier. The script is a record of
this run, not a reset helper: choose a fresh evidence directory when repeating it.

Documentation validation also passed: 167 local link targets existed, all three
Bash blocks parsed, the embedded Python block parsed, and the saved recipe
matched the guide's first two Bash blocks exactly. The saved tool hashes and
`git diff --check` passed. Link checking covered target files, not URL availability
or heading anchors.

**No new VM boot, Windows installation, account test, physical USB read/write or
Lenovo hardware test was performed in this recipe check.** The existing image was
attached read-only and was not rebuilt or modified. The earlier exact-image menu
boot and shutdown remain separate [dated evidence](../release-image-2026-09-19/README.md);
the original account/USB tests remain in the [September 18 report](../FINAL-REPORT.md).
This new integrity pass does not expand those historical claims.
