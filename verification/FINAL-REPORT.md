# Completed Windows 11 USB — September 18, 2026

The 64 GB Kingston DataTraveler 3.0, serial `4CEDFB74A32C1A70790301C3`, is written, flushed, verified, and unmounted. It booted from the physical USB into its account-choice menu in an isolated UEFI VM. The USB was opened read-only for this test, with no host internal disk or installation destination attached.

## Use

Press F12 and select the UEFI Kingston USB. Choose **1** for an interactive local account, staying disconnected until the desktop, or **2** for Microsoft account sign-in with networking. Remove the USB at the first installation restart or choose the internal Windows Boot Manager. Disk selection and deletion remain manual. No user account or password is embedded. See [the installation guide](../README.md).

## Evidence

- All **6,633 payload files** matched SHA-256 on physical readback. The checksum manifest itself also matches the finalized staging copy. FAT32 check passed.
- Offline Windows 11 Home reached its desktop with `PrincipalSource=Local` and Secure Boot enabled. Online Windows 11 Pro reached Microsoft's current account-entry form after OOBE updates; no credentials were supplied.
- The driver collection covers **49 machine types**, with **171 packages, 876 INF paths, and 73 network INF paths** for E485, L14/L15 factory variants, and T15g Gen 1 (20UR/20US).
- Windows imported all 415 distinct baseline INFs. A subsequent T15g test accepted all 90 additional INF inputs with PnPUtil exit code 0: 50 were already present and 40 distinct entries were added. [T15g validation](t15g-windows-validation/README.md). This later test is recorded here; the USB's documentation was finalized before it.
- [Physical USB menu screenshot](physical-usb-boot-02.png), [readback results](usb-readback-sha256.txt), [filesystem check](usb-filesystem-check.txt), and [machine-readable completion report](FINAL-RESULT.json).

The source ISO, staged payload, research, and evidence remain in this workspace. Large disposable VM disks were removed after their logs and screenshots were saved.

## Limits

Actual Lenovo laptop configurations were not reinstalled or physically tested. Factory driver coverage and Windows package acceptance do not certify every Wi-Fi, Ethernet, firmware, or RAID configuration. GPU acceleration and other optional components can be completed after reaching the desktop and internet. E485 processors are outside Microsoft's official Windows 11 CPU support, and Lenovo supplies that model's drivers for Windows 10.

The original Microsoft EFI loader uses the 2011 signing chain; firmware that has explicitly revoked that chain requires suitable 2023-signed media. See [Secure Boot notes](secureboot/README.md). The local path was tested on this exact image while offline; replacing the ISO or allowing online OOBE changes requires renewed testing.
