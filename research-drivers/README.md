# Lenovo bootstrap driver collection

Retrieved from Lenovo on 2026-09-18 for Windows 11 x64 installation media.

`bootstrap-drivers/` contains extracted, unmodified OEM driver payloads from 171 source packages: 876 INF files, including 73 network INF files, and 5.44 GiB of files. All 876 catalog-file references in the INFs resolve to files alongside the corresponding INF. The current computer's Qualcomm QCNFA765 `PCI\VEN_17CB&DEV_1103&SUBSYS_E0BE17AA` and Realtek Ethernet `PCI\VEN_10EC&DEV_8168&SUBSYS_509117AA` are explicitly represented.

Coverage is based on complete Lenovo model families, including factory Intel, Realtek, Qualcomm, and MediaTek WLAN variants found in the model catalogs, rather than just the connected computer's adapters. The machine types are:

| Family | Intel types | AMD types |
| --- | --- | --- |
| E485 | — | 20KU |
| T15g Gen 1 | 20UR, 20US | — |
| L14/L15 Gen 1 | 20U1, 20U2, 20U3, 20U4 | 20U5, 20U6, 20U7, 20U8 |
| L14/L15 Gen 2 | 20X1, 20X2, 20X3, 20X4 | 20X5, 20X6, 20X7, 20X8 |
| L14/L15 Gen 3 | 21C1, 21C2, 21C3, 21C4 | 21C5, 21C6, 21C7, 21C8 |
| L14/L15 Gen 4 | 21H1, 21H2, 21H3, 21H4 | 21H5, 21H6, 21H7, 21H8 |
| L14 Gen 5 | 21L1, 21L2 | 21L5, 21L6 |
| L14 Gen 6 | 21S6, 21S7 | 21S8, 21S9, 21SE, 21SF |
| L14 Gen 7 | 21X2, 21X3 | 21X6, 21X7 |

The collection includes network, chipset/platform, storage, power-management, USB/serial-I/O, mouse, and trackpoint driver packages. Windows supplies its ordinary NVMe/AHCI, USB, keyboard, and basic display drivers. The E485 AMD PSP and SMBus components come from the model's official SCCM package; its latest separate Qualcomm and Realtek WiFi packages replace the older/missing WiFi packages in that SCCM package. E485 drivers are published for Windows 10, so Windows 11 compatibility for this older platform requires actual-machine verification.

No BIOS or device-firmware updaters, WWAN/mobile-broadband packages, NPU drivers, GPU drivers, or optional applications were selected. The generic AMD S0i3 NetService network-filter package `r2ifc03w` was also omitted from automatic bootstrap because it is not required to reach the desktop or establish network connectivity. Two old AMD processor power provisioning packages (`r1kam04w`, `r1ypk01w`) contain only PPKG/EXE files and no INF, so were omitted from INF staging. Windows Update or Lenovo's model-specific update tools can complete optional hardware features after internet connectivity is working.

## Source and integrity records

- `driver-manifest.json`: every staged INF, its class/version/provider, SHA-256, hardware-ID tokens, source package URLs and SHA-256 values, and model catalog provenance.
- `model-coverage.tsv`: machine-type to selected package mappings and network package mappings.
- `hardware-ids.txt`: deduplicated hardware-ID tokens from the staged INFs. Some tokens are registry or commented references; the INF model sections remain the authority for matching.
- `source-checksums.sha256`: verified source installer checksums.
- `payload-validation.json`: all referenced catalog files present.
- `metadata/`: per-model catalogs and package XML descriptors. Each descriptor's SHA-256 was checked against its parent catalog; each downloaded installer was checked against its descriptor's SHA-256.
- `bootstrap-selected.json` and `bootstrap-excluded.json`: selection audit. `t15g-all-descriptors.json`, `t15g-selected.json`, and `t15g-excluded.json` record the added T15g audit.
- `catalogv2.xml`, `latest-packs.json`, and package readmes: official SCCM family/type mapping and fallback references.

The live catalog entry points were `https://download.lenovo.com/catalog/<type>_Win11.xml` (E485 uses `20ku_Win10.xml`) and `https://download.lenovo.com/cdrt/td/catalogv2.xml`. Package payloads and descriptors were fetched over HTTPS from `download.lenovo.com/pccbbs/mobiles/`.

Source package release dates range from 2020-05-07 (E485 Realtek LAN) through 2026-09-14. All catalogs were retrieved on 2026-09-18; older packages remain where Lenovo still lists them for older hardware. Individual INF DriverVer dates can be older, and Intel chipset naming INFs may intentionally use artificial historic dates. The separate catalogs were preferred over older SCCM snapshots where they offered newer driver releases. Source provenance and checksum/payload checks were performed; these are not a substitute for boot, OOBE, network, sleep, or device testing on every target laptop.

## Storage and WinPE review

All 403 unique package descriptors from the E485/L14/L15 model catalogs were separately audited regardless of their category (`all-descriptor-audit.json`, `storage-audit.log`). The only Intel Rapid Storage Technology package listed for those families is L14/L15 Gen 1 `r0zrs09w`, containing `iaAHCIC.inf` and `iaStorAC.inf`; no VMD/iaStorVD package was found for Intel Gen 2–7. The corresponding full SCCM readmes likewise list no such driver. Lenovo's official L14 Gen 5 and Gen 6 WinPE package readmes list Serial IO and Ethernet drivers, not RST/VMD storage drivers. This supports relying on Windows inbox storage drivers for those factory configurations; it is an inference from the current OEM deployment inventories, not an actual boot test of every BIOS/storage configuration.

For T15g Gen 1 (20UR/20US), all 36 current package descriptors were reviewed. Its [official hardware specification](https://psref.lenovo.com/syspool/Sys/PDF/ThinkPad/ThinkPad_T15g_Gen_1/ThinkPad_T15g_Gen_1_Spec.html) confirms the i7-10750H and RTX 2070 SUPER configuration, WM490 chipset, Intel AX201 WiFi, both I219-LM and I219-V Ethernet variants, and two NVMe slots with RAID 0/1 support. The collection includes both Ethernet variants, the AX201 WLAN driver, platform/chipset, management engine, Thunderbolt, USB-C power delivery, and input drivers. Basic display uses Windows' inbox driver; GPU acceleration can be installed after networking works.

T15g storage includes Lenovo's [RST 17.11.0.1000 package readme](https://download.lenovo.com/pccbbs/mobiles/n2idg13w.txt) and unmodified `n2idg13w_p` payload. The [current SCCM package readme](https://download.lenovo.com/pccbbs/mobiles/tp_p15_mt20st-20su-p17_mt20sn-20sq-t15g_mt20ur-20us_w11_22_202310.txt) independently lists the same storage package. It provides `iaAHCIC.inf`, `iaStorAC.inf`, related extension/software-component INFs, and the RST/Optane controller IDs, including `PCI\VEN_8086&DEV_06D6&CC_0104`, `PCI\VEN_8086&DEV_06D7&CC_0104`, and `PCI\VEN_8086&DEV_282A&CC_0104`. These are PCH/RST drivers; T15g Gen 1's catalog does not list a separate VMD driver. Some controller IDs overlap the newer L14/L15 Gen 1 RST package; Windows ranks matching drivers across the union, so model-specific RST payloads are also individually identifiable by directory for manual recovery if needed. No target T15g storage configuration has been physically tested here.

The staged tree has no zero-length catalog files and no case-insensitive relative-path collisions within a package. OEM subdirectory structure is retained. Where a source package contains different same-named files for different platforms or architectures, those remain in distinct original directories; payloads were not flattened or combined by basename.

Microsoft's [WinPE driver-loading limitations](https://learn.microsoft.com/en-us/troubleshoot/windows-client/setup-upgrade-and-drivers/limitations-dollar-sign-winpedriver-dollar-sign) explain that `$WinPEDriver$` attempts loading and schedules OS injection. Do not pre-load a different version of the same driver in `boot.wim` and then offer another version through `$WinPEDriver$`. This Microsoft article carries older underlying platform examples, so actual installation testing remains the stronger validation. Nonmatching physical-device drivers are subject to hardware matching, but a broad driver store is not equivalent to testing every combination.

A final unfiltered-category audit added seven essential I2C, PSP, HID, and platform-monitoring drivers catalogued by Lenovo under Software and Utilities. No further unselected chipset, I2C/GPIO/PSP/IOMMU, boot/storage, Ethernet, or WLAN drivers were identified in the current model descriptors.
