# Windows 11 installation USB for Lenovo ThinkPads

For maintainers, start with the [rebuild and refresh runbook](docs/runbook.md).
To produce a file for a USB flasher, follow [ready-to-flash image creation](docs/ready-to-flash-image.md).
Use [testing and acceptance](docs/testing-and-acceptance.md) for pass/fail criteria,
error diagnosis, independent image checks, and verification of each written USB.
The [documentation index](docs/README.md) links the account tests, driver
maintenance procedure, source/Secure Boot research, and lessons learned.
These guides explain which scripts are pinned to the September 18, 2026 build
and how to create fresh evidence without overwriting the recorded successful run.

Prepared September 18, 2026. English (United States), x64, Windows 11 25H2.
The Microsoft multi-edition installer includes Home and Pro; activation requires
the appropriate existing license or product key.

## Install

1. Connect the USB, turn on the ThinkPad, and press **F12** (or Enter, then F12).
   Select the **UEFI USB / Kingston DataTraveler** entry.
2. At the first menu choose **1: Local account** or **2: Microsoft account**.
   For a local account, unplug Ethernet and leave Wi-Fi disconnected until the
   desktop appears. Setup will ask for your own account name and password.
   For a Microsoft account, connect Ethernet or select Wi-Fi during setup.
3. Allow several minutes for initial driver discovery. Follow Windows Setup,
   select the licensed edition, and carefully select the
   intended installation disk. Disk selection and deletion are manual.
4. At the first installation restart, remove the USB or boot **Windows Boot
   Manager** on the internal disk. Reinsert the USB later if needed for drivers.
5. At the desktop, connect to the internet and run Windows Update, including
   applicable driver updates. Lenovo System Update can finish model-specific
   graphics, audio, and other features.

No account name, password, automatic login, product key, or destination disk is
preconfigured. This setup profile proceeds without entering a key during
installation; firmware/digital entitlement can activate the matching edition,
or you can enter your key later in Settings > System > Activation. You can switch between local and Microsoft sign-in afterward in
**Settings > Accounts > Your info**.

## Drivers

The `$WinPEDriver$` folder contains official Lenovo driver payloads for automatic
discovery by Windows Setup. It covers factory network variants and essential
platform/storage/input components for:

- E485, type 20KU.
- T15g Gen 1, types 20UR and 20US, including the i7-10750H / RTX 2070 SUPER configuration.
- L14 and L15 generations 1–4, Intel and AMD.
- L14 generations 5–7, Intel and AMD, including both AMD Gen 6 platform groups.

Intel, Realtek, Qualcomm and MediaTek Wi-Fi variants and the corresponding
Ethernet drivers are included. T15g Gen 1 includes Intel AX201 Wi-Fi, both I219-LM
and I219-V Ethernet, and its RST/Optane storage driver. Windows supplies its basic display and ordinary
NVMe/AHCI/USB drivers. This is bootstrap coverage for reaching a usable desktop
and internet access; a fully updated graphics/audio/optional-device installation
should be completed after connecting.

If Windows Setup cannot see the installation disk, use **Load driver** and browse
the driver folder. For T15g Gen 1 RAID/RST storage, its model-specific driver
is under `$WinPEDriver$\n2idg13w_p` (including `iaStorAC.inf`).
If networking is absent during OOBE, press **Shift+F10**
(sometimes **Fn+Shift+F10**), find the USB drive in the command prompt, and run
`Install-Drivers.cmd` from its root. At the desktop, right-click that file and
choose **Run as administrator**. It installs matching signed drivers, records a
log in `C:\Windows\Temp\Lenovo-bootstrap-drivers.log`, and does not force a reboot.

Exact machine types, package mappings, source hashes, and hardware IDs are listed
under `Documentation` on the finished USB.

## E485

The E485's original Ryzen processors are outside Microsoft's supported Windows
11 CPU list, and Lenovo publishes its drivers for Windows 10. Media preparation
does not make the platform officially supported or guarantee future updates.
Its real hardware still needs an installation/network check.

The optional `Enable-E485-Compatibility.cmd` is available from the installer's
troubleshooting command prompt if Setup blocks installation on eligibility
checks. It applies Rufus's three booted-install checks for that WinPE session;
it does not change firmware TPM/Secure Boot settings and is not run by default.

## Reproducibility

The base ISO is the file Microsoft's live download page supplied on September
18, 2026: `Win11_25H2_English_x64_v2.iso` (March 2026 media).
Microsoft's published SHA-256 is
`768984706B909479417B2368438909440F2967FF05C6A9195ED2667254E465E3`.

The boot image adds an account-choice menu. Separate answer files select the
documented OOBE account screens; local mode also sets the registry value used by
current Rufus. Setup Dynamic Update is disabled in these profiles so the
installation starts from the verified media. Windows Update remains available
after installation. Staying offline until the desktop keeps local setup from
being changed by online OOBE updates.

The install image is split into FAT32-compatible `.swm` files; Microsoft-signed
EFI boot files are retained. The USB is intended to boot in UEFI mode. Its original Microsoft boot files
use the Windows Production PCA 2011 signing chain, which favors older Lenovo
firmware. PCs that have explicitly revoked that certificate in their Secure
Boot DBX need 2023-signed media; see `Documentation/SecureBoot/README.md`.
Certificate expiration alone is not a reason to disable Secure Boot.

Validation results and dated research are recorded in `Documentation` on the
finished USB and in this workspace's `verification` directory.
