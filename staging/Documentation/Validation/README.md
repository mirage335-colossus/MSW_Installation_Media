# Validation record — September 18, 2026

The Microsoft Windows 11 25H2 US English x64 ISO matches the SHA-256 published on Microsoft’s live download page. Both the modified boot image and the split installation image passed wimlib resource verification. The installer retains Microsoft’s signed EFI boot files.

## Account tests

Two isolated UEFI virtual machines installed the actual prepared image onto disposable 80 GB disks. They retained interactive edition, EULA, locale, and destination-disk choices and booted independently after the installer USB was removed. The tested boot/image/profile hashes are recorded in account-tested-file-sha256.json.

- Windows 11 Home, local option, no network adapter: interactive local username and password screens, successful desktop, and PrincipalSource=Local. Confirm-SecureBootUEFI returned True.
- Windows 11 Pro, Microsoft option, internet through emulated Ethernet: validation evidence is recorded in cloud-test-notes.md and the accompanying screenshot. No Microsoft credentials were supplied.

Home/local and Pro/Microsoft are the tested combinations; all four edition/account combinations were not installed separately. Offline operation through the desktop is part of the local-mode instructions. A newer ISO or online OOBE update requires retesting.

## Driver tests

The final collection contains 171 source packages, 876 INF paths, and 73 network INF paths covering 49 Lenovo machine types. All 5,166 staged driver files match their source SHA-256 hashes. Every referenced catalog is present, with no empty catalogs or case-insensitive path collisions. Lenovo catalog descriptors and source installers were checked against their published SHA-256 values.

The full installation tests used the original 159-package E485/L14/L15 collection. Its 786 INF paths contain 415 distinct INF hashes. The installed Windows driver store contains matching per-class counts for all 415 entries, plus Microsoft’s printer driver. The final T15g additions underwent source and staging verification separately; the account launcher and installation images were unchanged. See final-driver-staging-validation.json and driver-store-comparison.json.

No E485, T15g, or alternative L14/L15 configuration was physically reinstalled to test its devices. Windows inbox drivers supply ordinary storage, USB, and basic display; optional GPU, audio, firmware and other features remain for Windows Update or Lenovo tools after connectivity. E485 processors are outside Microsoft’s supported CPU list, and its Lenovo drivers target Windows 10.

## USB checks

The writer verifies all staging hashes before formatting the uniquely identified 64 GB Kingston DataTraveler, flushes completed writes, remounts it read-only, verifies every listed file, checks FAT32, and unmounts it. The final physical-drive results are saved in the workspace verification directory after this document is written. A separate read-only boot smoke test uses the physical USB with no installation destination attached.

The USB uses one FAT32 partition and split .swm files so its standard Microsoft UEFI loader can boot directly. See ../SecureBoot/README.md for the distinction between 2011 signing-certificate expiration and actual firmware revocation. The successful Secure Boot VM test used firmware that trusts Microsoft’s 2011 chain; it does not certify every Lenovo firmware DB/DBX state.
