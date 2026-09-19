# Source media, boot compatibility, and rebuild constraints

This document describes the **September 18, 2026 build and validation snapshot**. It does not assert that Microsoft's downloads, account setup, firmware guidance, or signing policy remained unchanged on September 19 or any later date. External links identify the sources consulted; the local evidence records what was acquired and tested.

## Exact Microsoft source

The [Microsoft Windows 11 download page](https://www.microsoft.com/en-us/software-download/windows11) identified its release as Windows 11 2025 Update, version 25H2. Its live browser flow, with **Windows 11 multi-edition ISO for x64 devices** and **English (United States)** selected, supplied:

| Field | Recorded value |
| --- | --- |
| Filename | `Win11_25H2_English_x64_v2.iso` |
| Download host | `software.download.prss.microsoft.com` |
| Length | 8,471,603,200 bytes |
| ISO volume | `CCCOMA_X64FRE_EN-US_DV9` |
| ISO creation date | March 7, 2026 |
| Installed Windows version | 10.0.26200.8037 |
| Boot image version | 10.0.26100.8037 |
| Checksum verified | September 18, 2026, 19:36:47 UTC |

The live page's **English 64-bit** verification row and the completed download both gave SHA-256:

```text
768984706b909479417b2368438909440f2967ff05c6a9195ed2667254e465e3
```

The age of the ISO was established by its contents, rather than inferred from the date of the web request. This was the image the official page actually delivered on the acquisition date. The two different build numbers above are the values recorded in the installation and boot WIMs, respectively.

Evidence: [acquisition provenance](../downloads/windows11-iso-provenance.json), [checksum companion](../downloads/Win11_25H2_English_x64_v2.iso.sha256), [complete ISO listing](../verification/official-windows11-iso-file-list.txt), [installation image metadata](../verification/install-image-info.txt), and [boot image metadata](../verification/boot-image-info.txt).

From the repository root, this rechecks an already acquired copy without downloading or modifying it:

```bash
set -euo pipefail
(cd downloads && sha256sum -c Win11_25H2_English_x64_v2.iso.sha256)
```

The checksum companion uses a filename relative to `downloads`; checking it from a different working directory without adjusting the path fails. [prepare-media.py](../scripts/prepare-media.py) independently computes and enforces the same source hash before extraction. A newer ISO must receive its own provenance, build inspection, and complete account/boot tests; changing only the expected hash does not transfer the old validation result.

## Acquisition lessons

Shell requests to Microsoft's HTML download page and `software-download-connector` API returned HTTP 403. Inspection of the open-source [Fido implementation](https://github.com/pbatard/Fido) helped identify the public download sequence, but its scripted sequence also received 403 at the SKU API. Fido was read as reference code and was not executed.

The ordinary Microsoft page in the browser succeeded. The first browser call timed out, but the page had loaded; inspecting the existing tab recovered that session without restarting the selection flow. After edition and language selection, the page generated an HTTPS link on Microsoft's `software.download.prss.microsoft.com` CDN. `curl` successfully downloaded that exact link. Thus the 403 was a download-page/API obstacle; the selected CDN file was accessible and did not require a third-party mirror.

The generated link expired at `2026-09-19T19:30:55.9909284Z`. It is not a durable rebuild input. Future acquisition should obtain a fresh link from the official flow, preserve the exact filename and live hash row, download, then compare the complete SHA-256. Do not substitute an image from a mirror merely because the filename looks right. The retained [acquisition notes](../research/iso-acquisition/README.md) describe the sequence; temporary page captures and Fido source are deliberately excluded from version control.

An additional measurement lesson: inspecting the incomplete ISO initially reported a size 2,048 bytes below the completed file. The final provenance uses the completed file's size. Partial-download metadata was not used as the integrity check.

## WIM handling and FAT32 layout

The ISO contains 11 installation images. These indices apply to this ISO only:

| Index | Edition |
| --- | --- |
| 1 | Windows 11 Home |
| 2 | Home N |
| 3 | Home Single Language |
| 4 | Education |
| 5 | Education N |
| 6 | Pro |
| 7 | Pro N |
| 8 | Pro Education |
| 9 | Pro Education N |
| 10 | Pro for Workstations |
| 11 | Pro N for Workstations |

The boot WIM has two images: index 1 is Windows PE, and **index 2 is Windows Setup and the configured boot index**. Preparation injects `MediaSetup.cmd` and `winpeshl.ini` into `Windows/System32` of index 2. Editing index 1 alone would not alter the Setup image that this media boots. The source installation WIM was 7,578,046,378 bytes; it was split because it exceeds FAT32's maximum file size of 4,294,967,295 bytes.

The relevant commands in [prepare-media.py](../scripts/prepare-media.py) are equivalent to:

```bash
set -euo pipefail
wimlib-imagex info staging/sources/install.wim
wimlib-imagex info staging/sources/boot.wim
wimlib-imagex verify staging/sources/boot.wim
wimlib-imagex split staging/sources/install.wim staging/sources/install.swm 3800 --check
wimlib-imagex verify staging/sources/install.swm '--ref=staging/sources/install*.swm'
```

The `info` command for `install.wim` and the `split` command require the original extracted `install.wim`, which the preparation script deletes **after** successful split verification. Those commands cannot run against the completed staging tree as it stands. The quoted `--ref` leaves the split-part pattern for wimlib to resolve; all parts must remain together.

Final recorded file sizes were:

| File | Bytes |
| --- | ---: |
| `sources/boot.wim`, after customization | 622,059,570 |
| `sources/install.swm` | 3,462,502,600 |
| `sources/install2.swm` | 3,968,629,487 |
| `sources/install3.swm` | 82,849,248 |

All 11 installation editions remain available. Splitting changes storage, not edition choice. Disk selection, edition selection, and account identity remain interactive. See [split verification](../verification/install-swm-verify.txt), [boot WIM verification](../verification/boot-wim-verify.txt), and the [tested file hashes](../verification/account-tested-file-sha256.json).

The physical USB was assembled as a filesystem, rather than copied byte-for-byte from the ISO. Both [build-test-media.sh](../scripts/build-test-media.sh) and [write-verified-usb.sh](../scripts/write-verified-usb.sh) create a DOS/MBR table with one partition starting at sector 2048, type `0c`, marked bootable; `mkfs.vfat -F 32 -s 64 -n MSW11LENOVO` creates FAT32 with 32 KiB clusters on this 512-byte-sector device. The filesystem receives the staged files, including Microsoft's EFI loader at `efi/boot/bootx64.efi`. Validation was for **UEFI boot**, not a promise of legacy BIOS boot support.

The exact target capacity was 61,991,813,120 bytes. The [final partition table](../verification/usb-final-partition-table.txt) and [filesystem check](../verification/usb-filesystem-check.txt) record the completed layout. The finalized payload comprised 6,633 files and 14,275,404,386 bytes before filesystem overhead; every listed file was hashed again from the physical USB. The manifest itself was checked separately: [readback](../verification/usb-readback-sha256.txt), [manifest check](../verification/physical-checksum-manifest.json), and [finalized payload record](../verification/validation-ready.json).

## Secure Boot: inspect the certificate, not the name

The retained default `efi/boot/bootx64.efi`, root `bootmgfw.efi`, and root `bootmgr.efi` contain a signing chain through **Microsoft Windows Production PCA 2011**, issued by Microsoft Root Certificate Authority 2010. The default `bootx64.efi` has SHA-256 `32b233afb2a8b4c517003796d435358dcad78e421a3ed386b8ee275a6957dbd0`.

Inspection decoded each PE security directory, extracted its PKCS7 data, and printed the certificates with OpenSSL. This identifies the contained signing chain; it is not an independent Authenticode verification or a reading of any target Lenovo's firmware DB/DBX. Source authenticity was established by the full ISO hash. Raw certificates, dates, and per-file hashes remain in [certificates-summary.json](../verification/secureboot/certificates-summary.json) and the adjacent `.p7`/`.txt` files.

The default bootx64 leaf certificate's expiry was June 17, 2026, while its PCA2011 authority's expiry was October 19, 2026. As explained in the Microsoft guidance consulted on September 18, **certificate expiry alone does not stop an existing device from starting**; lack of migrated trust affects new boot-security protections. Some devices need vendor firmware updates for migration. [Microsoft KB5079373](https://support.microsoft.com/en-us/servicing/os/secure-boot/2026/02/when-secure-boot-certificates-expire-on-windows-devices).

**Revocation is a separate condition.** A firmware DBX that explicitly rejects Windows Production PCA 2011 blocks boot managers under that authority. Merely adding Windows UEFI CA 2023 to the allowed DB does not itself revoke 2011. Secure Version Number restrictions can also reject an older boot manager. The default media therefore retains a useful compatibility path for older firmware still trusting PCA2011, but it cannot be promised to boot firmware that has revoked it. [Microsoft KB5025885](https://support.microsoft.com/en-gb/servicing/os/windows/2023/03/how-to-manage-the-windows-boot-manager-revocations-for-secure-boot-changes-associated-with-cve-2023).

The same installation WIM contains `Windows/Boot/EFI_EX/bootmgfw_EX.efi` signed through **Windows UEFI CA 2023**, hash `d15b56f8800fa95efeeb63fb7b0891176fd40e447c10e44c3619e079487cd599`. However, adjacent `bootmgr_EX.efi` still chains to PCA2011. An `_EX` suffix is not sufficient evidence of its certificate. Those files were extracted for inspection and did not replace the default loader. The disposable copies are excluded from Git and must be re-extracted from the verified ISO if needed.

Microsoft's documented 2023-media route is `Make2023BootableMedia.ps1` with the ADK and suitably serviced input media. A rebuilt 2023 path needs its own validation against firmware trusting Windows UEFI CA 2023; copying a conveniently named file is not the procedure demonstrated by this project. [Microsoft KB5053484](https://support.microsoft.com/en-us/servicing/os/windows/2025/02/updating-windows-bootable-media-to-use-the-pca2023-signed-boot-manager).

The dated [Lenovo research notes](../verification/secureboot/README.md) include L14/L15 minimum BIOS examples from Lenovo HT518129. A version containing new factory-default certificates does not prove those certificates are active in an individual machine's DB. E485 migration support was not established by the retrieved table. No firmware reset, key enrollment, or Secure Boot change was performed on a physical Lenovo as part of this work.

## Reproduce the checks, with the actual script boundaries

The Linux workflow expects Python 3.11 or later (`hashlib.file_digest`), 7-Zip, wimlib, rsync, util-linux disk tools, dosfstools, QEMU/KVM, OVMF with Microsoft-enrolled variables, swtpm, and Pillow for screenshot conversion. The VM launchers use `/dev/kvm`, `-cpu host`, and Debian-style `/usr/share/OVMF/` paths; they have no software-emulation or other-host fallback. Disk/loop access needs the appropriate elevated permissions. Ordinary media preparation does not require elevated privileges.

| Script | Actual responsibility and limitation |
| --- | --- |
| [prepare-media.py](../scripts/prepare-media.py) | Verifies the pinned ISO, extracts it, updates boot WIM index 2, copies account/helper files, validates profiles, splits and verifies the installation image. It does not acquire the ISO, download/stage the driver collection, initialize VMs, or populate every final documentation artifact. |
| [build-test-media.sh](../scripts/build-test-media.sh) | Builds a sparse USB-sized image using a loop device and copies the current staging tree. Refuses an existing `verification/test-usb.img`. It is not itself a full checksum readback test. |
| [build-release-image.sh](../scripts/build-release-image.sh) | Packages finalized staging into a fresh whole-device `.img`, verifies its exact payload and geometry through read-only reattachment, and writes image SHA-256/report files. It consumes recorded account evidence; its separate boot test is described in the [image guide](ready-to-flash-image.md). |
| [start-test-vm.sh](../scripts/start-test-vm.sh) | Starts `local` or `cloud` against the prepared read-only test image, a writable disposable `system.qcow2`, per-test OVMF variables, and swtpm state. Local has no NIC; cloud uses emulated Ethernet and QEMU user networking. |
| [finalize-media.py](../scripts/finalize-media.py) | Compares supplied tested-file hashes, checks expected evidence files and driver-validation fields, then produces the full manifest and `validation-ready.json`. It consumes test evidence; it does not execute or independently judge the account tests. |
| [write-verified-usb.sh](../scripts/write-verified-usb.sh) | Destructively writes only the fixed Kingston identity after its gates, then flushes, remounts read-only, checks hashes and FAT32, and unmounts. It is not a generic arbitrary-drive writer. |
| [start-physical-usb-test.sh](../scripts/start-physical-usb-test.sh) | Starts a separate read-only physical-USB smoke test with no network or installation destination. Requires the completed writer's evidence files and refuses an existing test directory. |

The account VM inputs are not initialized by an existing script. Each run requires a new disposable disk of at least Windows' required capacity, an independent copy of `OVMF_VARS_4M.ms.fd`, and a writable swtpm state directory. The historical tests used disks described in their notes as 80 GB. Preserve old evidence and confirm its VM/TPM processes have stopped before replacing per-run paths. New TPM state should accompany new firmware variables and a new guest disk. Starting the retained launcher alone after cloning is insufficient.

The original disposable test image and VM disks were intentionally removed after exporting evidence. Their removal is recorded in [FINAL-RESULT.json](../verification/FINAL-RESULT.json). This was cleanup, not a failed build. Do not reinterpret the remaining historical screenshots or the copied validation-ready record as evidence for a newly built image.

The physical smoke launcher takes a stronger approach than relying on a filename. It validates the fixed serial/capacity/USB/removable identity, checks that its partitions are unmounted, opens both `host_device` and `raw` block layers with `read-only=on`, and starts the CPU paused. QMP checks every backing filename against the USB and the two firmware files, verifies both USB layers are read-only, then resumes. No guest installation disk or network adapter is attached. The [saved block graph](../verification/physical-boot/block-graph-before-boot.json) shows both USB layers `ro: true`; only the private firmware-variable copy is writable. The [physical menu screenshot](../verification/physical-usb-boot-02.png) records successful boot. This is not a physical Lenovo Wi-Fi/Ethernet test or a full installation from the actual stick.

The physical smoke test used Microsoft-enrolled OVMF code hash `1a46295574430cfb7f825ee3e4dc64b052acbef08e310377ed7c64cb757a9dc1` and initial variables hash `0d12f9839018a68f4b13c9819cbf607b8b62d566f9c9dd7966550d93335f06b2`. [Firmware evidence](../verification/physical-boot/firmware-start-sha256.txt). Separately, the [offline Home installation](../verification/local/test-notes.md) reached its desktop and reported `Confirm-SecureBootUEFI=True`; the [connected Pro installation](../verification/cloud/test-notes.md) reached Microsoft's sign-in form without credentials. Their differing endpoints must remain explicit.

## Gaps to account for before another run

- **Preparation is not idempotent.** A normal run refuses an existing `staging/sources`. `--resume` skips extraction but still expects `install.wim`; after successful preparation that file has been deleted. Resume is only appropriate to an understood partial state. Use a fresh build tree or restore verified source media deliberately, preserving prior evidence.
- **Source inputs and validated outputs differ.** A new WIM update may produce different derived hashes through metadata changes. The old hashes bind the old tested candidate, rather than certifying an arbitrary rebuild. Refresh the tested-file record only after new tests, then finalize again.
- **Finalization has snapshot-specific assumptions.** It expects 5,166 compared driver files and particular evidence filenames. Its account-success field is emitted after those checks, not after interpreting screenshots or driving OOBE. Driver changes and new test runs need new reviewed evidence; simply reusing old JSON is inadequate.
- **Assertions are real gates only in normal Python mode.** These scripts use Python `assert` for important checks. Do not invoke them with `python -O` or inherited `PYTHONOPTIMIZE`. A future general-purpose version should make mandatory safety failures explicit exceptions independent of optimization.
- **The writer's `lsblk --tree` is intentional.** On this host, JSON with `PATH` but no tree flag flattened disk and partition into separate top-level entries. The current writer includes `--tree`, so identity and recursive mount checks see the intended topology.
- **The manifest does not automatically reject every unlisted addition.** Finalization hashes all files then present, but the writer verifies the listed files and the bound manifest; it does not independently compare the complete current pathname set with the manifest. Keep staging unchanged after finalization and regenerate/review if anything is added. Runtime processes also need cleanup after failed starts; the account launcher does not implement complete QEMU/swtpm rollback.
- **Physical-test reruns preserve state by refusing reuse.** `verification/physical-boot` already exists in the evidence checkout. Archive a completed run before making a fresh one. Never delete or overwrite its variables to get past the guard while its VM may be running. The launcher starts a root-owned QMP socket, so its monitor commands require the corresponding privileges.

[.gitignore](../.gitignore) deliberately excludes ISO/WIM/SWM and virtual-disk payloads, extracted vendor trees, staged Microsoft binaries, mount directories, and mutable VM firmware/TPM/socket/PID state. It keeps scripts, profiles, source metadata, manifests, screenshots, and reports. The `.iso.sha256` companion remains eligible for Git. Consequently a clone is a recipe and an evidence archive, not a runnable installation medium or a ready-to-start VM. The large ignored payloads must be reacquired or rebuilt, and their new results verified. Ignore rules do not untrack files already committed; use `git ls-files` and `git check-ignore -v` when reviewing repository contents.
