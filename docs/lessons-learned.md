# Lessons and troubleshooting from the installer builds

These observations cover the September 18 USB build and September 19 release-image
workflow tests. They are dated results and maintenance cautions, not timeless Windows
behavior. For exact sources and test procedures, use the [account guide](account-choice-and-testing.md),
[driver guide](driver-maintenance.md), and [source-media guide](source-media-and-secure-boot.md).

| Observation or failure | What worked / how to handle it next time |
| --- | --- |
| Official account documentation was years old; community bypass reports could change within days. | Date the sources, inspect current upstream implementations, then test the exact downloaded ISO. Keep an offline local-account path and a separate ordinary online path. Recheck a new ISO or changed online OOBE. |
| Removing a Microsoft-account requirement is different from precreating a named account. | Use explicit menu-selected profiles. Keep name/password, disk selection, edition, EULA and privacy choices interactive. No preset user, password, auto-logon, root `autounattend.xml`, or silent disk layout. |
| `/DiagnosticPrompt Enable` was documented for newer WinPE but this media's `sources/setup.exe` rejected it with exit code 31. | Remove that argument; the tested launcher uses `/unattend:` only. Shift+F10 worked without the rejected argument. This is exact-binary evidence, not a universal claim about every Setup version. |
| `choice.exe`, `findstr.exe`, and an original `winpeshl.ini` were absent from boot.wim index 2. | Inspect the actual WinPE image. The launcher uses CMD built-ins, and extraction of optional original files uses `--nullglob`. Do not assume a desktop utility exists in WinPE. |
| Unsafe interpolation of menu input can turn text into CMD syntax. | Retain the reviewed delayed-expansion comparisons; never execute or CALL the entered text. Find the USB through a unique exact marker, and reject duplicate matching media. |
| Setup CLI `/DynamicUpdate` is not the WinPE control used here. | Set DynamicUpdate in the answer file. This controls Setup; online OOBE still updated and restarted independently. Keep local mode disconnected through desktop. |
| Empty ProductKey/Key was needed by the chosen answer-file pattern; the tested UI went to edition selection without a key-entry screen. | Preserve the tested structure unless retesting it. Choose a properly licensed edition and activate using entitlement or a key afterward. Do not auto-accept license terms or add a key to the repo. |
| Initial installation and first-boot driver processing took many minutes. | Watch screenshots and disk/log progress before declaring a hang. Two successful installs took roughly tens of minutes each. A large cross-model driver store changes timing substantially. |
| Rebooting with USB first in boot order returned to the account menu. | Remove/detach the installer at the first installation restart, then boot the internal Windows Boot Manager. Menu reappearance did not mean the installation had failed. |
| Shift+F10 could open a console behind OOBE, and OOBE could reclaim focus. | Take a screenshot, wait for redraw, focus the existing console before typing, and avoid opening many consoles. Use observed UI state rather than fixed sleeps alone. |
| A VM-only FAT log disk was not assigned a letter when presented as fixed storage. | Reattach it with `removable=on`; confirm its label with `Get-Volume` before writing. Drive letters change between WinPE and installed Windows. |
| Lenovo categories hid essential I2C, PSP, HID and platform components under Software and Utilities. | Audit all descriptors, not just Network/Storage/Chipset categories. Seven essential packages were added after this audit. Keep the E485 and T15g audits separate from the L14/L15 403-descriptor audit. |
| One observed L15 had Qualcomm Wi-Fi and Realtek Ethernet, but other factory variants differed. | Use the full machine-type/model catalogs. Include relevant Intel, Realtek, Qualcomm and MediaTek WLAN alternatives plus Ethernet and essential platform/storage/input drivers. |
| OEM packages contained different same-named files for architectures or subcomponents. | Preserve package-relative directory structure. Do not flatten by basename. Check every CatalogFile reference, empty catalogs, case-insensitive path collisions, and source/staged file hashes. |
| T15g and L14/L15 Gen 1 RST packages share some controller IDs. | Preserve both model-identifiable folders and document that Windows ranks matching drivers. Keep the T15g `n2idg13w_p` folder available for manual Load Driver; test real RAID configurations separately. |
| 876 INF paths did not mean 876 distinct imported drivers. | Count hashes, package dependencies, and driver-store entries separately. Baseline: 786 paths / 415 unique INFs; final: 876 paths / 455 unique INFs. Microsoft's printer accounts for the extra installed entry. |
| T15g was added after full account installs had begun. | Retain the exact unchanged boot/image/profile hashes, verify the added payload separately, and record the scope split. Windows subsequently accepted all 90 T15g INF inputs (50 shared + 40 new) with exit 0 and Secure Boot on. A normal new run should assemble all final drivers before starting full installs. |
| Default Microsoft EFI files used the 2011 signing chain even though their signing certificates were expiring in 2026. | Distinguish expiration from firmware DBX revocation. Secure Boot remained enabled in the successful VM. Do not disable Secure Boot or blindly substitute an `EX`-named binary; inspect the actual chain and current servicing procedure. |
| `lsblk -J -o PATH,...` returned disk and partition as separate top-level entries. | Include `--tree` when checking identity and recursively checking mounted children. The writer's fail-closed assertion caught this before formatting. |
| A 64 GB marketed USB was 61,991,813,120 bytes (57.73 GiB). | Match exact bytes, serial, model, USB transport and removable status. Preserve the fixed by-id guards; `/dev/sda` alone is not a safe device identity. |
| FAT32 cannot store a single file of 4 GiB or larger. | Split install.wim at 3800 MiB, verify all split resources, and use the standard Microsoft UEFI loader. The 64 GB FAT32/MBR geometry was boot-tested; legacy BIOS boot is not promised. |
| Rsync reached 100% while several gigabytes remained buffered. | Treat progress as bytes copied into the OS, not durable media completion. Wait for `sync -f`, unmount and buffer flush. This drive took substantially longer than the displayed copy ETA; budget roughly 35 minutes for write/flush/readback on the observed slow drive, with additional boot-test time. |
| Progress logs used carriage returns and appeared as enormous single lines to `tail`/`rg`. | Use Python `read_text().splitlines()[-N:]` for a short view. Avoid dumping entire progress lines or logs into a tool response. |
| A readback check must use the finished physical drive. | Remount read-only after flushing; check every payload hash and the checksum manifest itself, run read-only fsck, then boot the actual USB read-only with no destination disk attached. |
| A QMP request briefly failed due to an automatic approval-review timeout. | It was a tooling delay, not evidence of a stuck Windows install. Retry only as permitted and inspect actual VM progress. Keep raw devices/QMP privileged only where needed. |
| Review of the repeat-run recipe found that long `.runs/<date-label>` paths exceed Linux Unix-domain socket limits. | Check the resolved, encoded path of every QMP/swtpm socket, including the longer T15g validation path. Use a short actual run root; a symlink may be resolved back to the long path. This was a documentation-review finding, not a failure in the original completed run. |
| The scripts depend on assertions, old counts, fixed filenames and human evidence. | Do not use Python optimization. `finalize-media.py` is not an automated OOBE tester: old screenshots and reports must never be used to certify a new build. See the runbook's release gates. |
| Successful preparation removes install.wim; successful cleanup removes VM disks. | `prepare-media.py --resume` is for an inspected partial failure, not rerunning a completed build. Use a new workspace, freshly extract the ISO, and recreate VM disks/firmware/TPM state. |
| The account-test image was created before final documentation and the checksum manifest. | Build a new release image from finalized staging. Verify its exact file set, all bytes, geometry and whole-image hash, then boot that exact image read-only. Renaming `test-usb.img` cannot add missing release files. |
| The historical eight account hashes omitted other Setup resources and driver files. | For future runs, snapshot and verify the entire candidate before testing; compare final functional payload with it and list allowed documentation changes. Preserve the historical test scope instead of fabricating a retrospective snapshot. |
| Sparse host images still describe every zero byte of a 62 GB disk. | Store them on a filesystem that supports their logical size. Raw flashing writes the full image, so its ETA differs from copying 14 GB of files. Never skip zero writes on a physical USB; verify exactly the image length on readback. |
| The first release-image integration test could not read the root-owned FAT remount under a restrictive mask. | Set explicit invoking-user `uid`/`gid` and readable masks on read-only mounts too. Make directory enumeration errors fail explicitly; Python `os.walk` otherwise skips unreadable trees. The incomplete image was never published. |
| A strict equality check rejected a valid FAT volume after all file and filesystem checks passed. | `mkfs.fat` rounds volume sectors down to whole tracks. With the pinned 255/63 geometry, require 121,075,668 FAT sectors inside the 121,075,712-sector partition (44 unused sectors), while continuing to reject overruns and other size mismatches. |

## Record limitations alongside successes

The original full tests exercised Home/local and Pro/Microsoft. The online test
stopped at an empty sign-in form; authentication and a cloud-account desktop were
not tested. All software-driver acceptance tests used emulated hardware, and do
not establish real Lenovo network, storage, firmware or power behavior. E485's
original CPUs are outside the official Windows 11 list and its OEM drivers are
Windows 10 packages. Keep these limits in future reports rather than translating
package acceptance or a VM boot into a claim of universal laptop support.

The first local installation's `setuperr.log` was not empty: MultiEdition-key
cleanup, lack of the 2023 certificate in the VM firmware DB, and system-disk
detection entries remained despite a successful independent boot and desktop.
Compare logs with the observed outcome and investigate new errors; neither
“any error text means failure” nor “the desktop appeared, so ignore all errors”
is a sufficient rule.
