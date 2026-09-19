# Account choice and installation testing

Recorded September 19, 2026 from the September 18 build and tests. This document describes observed behavior of that media, not a guarantee that a later Windows build or online OOBE update behaves the same way. OOBE is Windows' first-run account and device setup.

## What was built

The boot menu asks for the desired account type before launching Windows Setup. It passes one answer file explicitly; there is no root `autounattend.xml` that silently chooses a path. No username, password, automatic login, product key value, or installation destination is embedded.

| Component | Role |
| --- | --- |
| [winpeshl.ini](../research-accounts/winpeshl.ini) | In `boot.wim` index 2, runs `wpeinit.exe`, then the command-script menu. The source image had no existing `winpeshl.ini`. |
| [MediaSetup.cmd](../research-accounts/MediaSetup.cmd) | Finds the USB by the first line of `MSW11-MEDIA.ID`, checks both profiles and `sources\setup.exe`, and presents local, Microsoft, troubleshooting, and shutdown choices. |
| [local.xml](../research-accounts/profiles/local.xml) | Sets `BypassNRO=1` during `specialize`; sets `HideOnlineAccountScreens` and `HideWirelessSetupInOOBE` to `true` during `oobeSystem`. |
| [microsoft.xml](../research-accounts/profiles/microsoft.xml) | Sets both OOBE screen-hiding values to `false`; does not set `BypassNRO`. |

The launcher runs the selected media binary with only the supported argument used in the successful test:

```bat
start "" /wait "%MSW11_MEDIA%\sources\setup.exe" /unattend:"%MSW11_MEDIA%\profiles\%MSW11_PROFILE%.xml"
```

Both profiles disable **Setup Dynamic Update** through the `windowsPE` XML setting. They retain an empty `UserData/ProductKey/Key` element and `WillShowUI=OnError`, following Rufus's comment about WinPE product-key validation. The empty element is not a license or activation key. The observed edition chooser and EULA remained interactive. Neither profile contains `DiskConfiguration`, `ImageInstall`, `UserAccounts`, `AutoLogon`, `SkipMachineOOBE`, or `SkipUserOOBE`.

The menu's local-account instruction is part of the tested procedure: disconnect Ethernet and leave Wi-Fi disconnected until the desktop. The Home test enforced this by giving the VM **no network adapter**. The combined local profile worked under that condition; the test did not isolate which individual setting was necessary or prove that local mode works while connected.

Disabling Setup Dynamic Update does not disable Windows Update or prevent OOBE from updating itself. The connected Pro test demonstrated this: OOBE performed an initial update and restart, then later offered another Windows-update stage. Staying offline preserves the tested local setup environment. Connect after the desktop for Windows and driver updates. Either account type can subsequently be changed through Settings > Accounts > Your info, subject to Windows' current behavior.

The optional [E485 compatibility helper](../research-accounts/Enable-E485-Compatibility.cmd) is separate from account selection. It is not invoked by default and was not needed in the account VMs. It applies the three documented-in-Rufus `LabConfig` installer checks, not firmware TPM/Secure Boot changes. The E485's unsupported CPU status remains a separate hardware limitation.

## Exact test matrix and evidence

The source was `Win11_25H2_English_x64_v2.iso`, Windows 11 25H2 US English x64, build **26200.8037**. Microsoft's live download page supplied this March 2026 media on September 18. The published and calculated SHA-256 matched:

```text
768984706b909479417b2368438909440f2967ff05c6a9195ed2667254e465e3
```

See [ISO provenance](../downloads/windows11-iso-provenance.json) and [account-tested file hashes](../verification/account-tested-file-sha256.json). Those eight historical hashes identify the modified boot WIM, split install image, default EFI loader, marker, and profiles used by the September 18 account tests. They do not cover every functional file: the externally launched `sources/setup.exe`, its other Setup resources, additional EFI/BCD files, and drivers are outside that eight-file list. Do not describe it as a full candidate-payload snapshot. A filename or download date alone does not identify the tested content.

| Test | Configuration and endpoint | Result and preserved evidence |
| --- | --- | --- |
| Home / local | Menu 1; 80 GB disposable virtual disk; no NIC; UEFI/TPM VM. Create a disposable local user and reach the desktop. | **Passed.** [User creation](../verification/local/42-local-account.png), [password prompt](../verification/local/43-password.png), [desktop](../verification/local/51-desktop-progress.png), [notes](../verification/local/test-notes.md). `MediaTest` existed only in the VM. |
| Local identity and Secure Boot | Elevated diagnostics on the Home desktop. | **Passed.** `Get-LocalUser` reported `PrincipalSource=Local`; `Confirm-SecureBootUEFI` returned `True`. [Diagnostic screenshot](../verification/local/54-diagnostic-results.png), [account export](../verification/local/exported/account.txt), [Secure Boot export](../verification/local/exported/secureboot.txt). The text exports are UTF-16. |
| Pro / Microsoft | Menu 2; 80 GB disposable virtual disk; emulated e1000e Ethernet with QEMU user networking; personal-use OOBE. Stop at account entry. | **Passed to sign-in form.** [Empty Microsoft account form](../verification/cloud/63-microsoft-signin.png), [notes](../verification/cloud/test-notes.md). No credentials entered. Authentication and a Microsoft-account desktop were not tested. |
| Installation controls and independent boot | Both account VMs. | Locale, edition, EULA, disk selection and applicable privacy/account choices remained interactive. Both installed to the blank virtual disk and booted Windows after the installer USB was detached. |
| Other account combinations | Pro/local and Home/Microsoft; connected local mode. | **Not run.** The two passes above must not be described as testing every edition/account/network combination. |
| Physical USB boot | Finished USB opened read-only in a separate UEFI VM, with no installation destination or NIC. | **Passed to the menu.** [Menu screenshot](../verification/physical-usb-boot-02.png), [block graph](../verification/physical-boot/block-graph-before-boot.json). This was not a physical Lenovo laptop test or another full installation. |

The full installation tests used the 159-package driver baseline. Windows imported the 415 distinct baseline INF hashes; the 416th third-party entry was Microsoft's printer INF. The [driver-store comparison](../verification/local/driver-store-comparison.json) records count and class agreement, not physical device function.

The final media included 12 additional T15g packages after those account tests. Their 90 INF inputs were tested later in the existing Home VM using PnPUtil: all were accepted, 50 were already present, and 40 distinct entries were added. See the [separate T15g validation](../verification/t15g-windows-validation/README.md) and [summary](../verification/t15g-windows-validation/validation-summary.json). This did not rerun Setup with the expanded bundle. The unchanged account components and final driver staging were checked separately; see [final staging validation](../verification/final-driver-staging-validation.json).

All 6,633 final payload files passed physical USB SHA-256 readback and FAT32 checking; the checksum manifest itself also matched. The [final report](../verification/FINAL-REPORT.md) and [machine-readable result](../verification/FINAL-RESULT.json) record that scope. Actual Lenovo storage configurations, firmware, Wi-Fi, Ethernet, and driver binding remain untested. Secure Boot `True` in the VM does not establish compatibility with every laptop's firmware trust/revocation database; see [Secure Boot inspection](../verification/secureboot/README.md).

## Lessons from failures and misleading signals

| Observation | Change or operating lesson |
| --- | --- |
| Microsoft's general CLI reference listed `/DiagnosticPrompt Enable` for WinPE, but this ISO's `sources\setup.exe` rejected it and exited with code 31. | Removed the argument, rebuilt the boot WIM and test image, and restarted both tests from blank disks. The corrected binary accepted `/unattend:`. Shift+F10 worked without the rejected option. Preserve [the failure screenshot](../verification/cloud/03-setup.png); do not reintroduce the argument based only on the reference page. |
| The actual boot image lacked `choice.exe` and `findstr.exe`. | Replaced both dependencies with CMD built-ins. Read menu input and the marker with `set /p`, and compare exact values using delayed expansion. Do not assume a full Windows command inventory exists in WinPE. |
| Marker parsing used a nested `setlocal`. | End the nested scope before assigning the caller's `MSW11_MEDIA` and duplicate flag. Otherwise a seemingly successful lookup loses the selected drive when it returns. The drive argument comes only from a fixed list. |
| User input can contain CMD metacharacters. | Keep the current exact `1`/`2`/`3`/`4` delayed-expansion comparisons. Do not execute input, pass it to `CALL`, or replace the comparisons with percent-expanded input in a parsed command. |
| Setup displayed a black/blank screen or a purple background without its main panel. | Initial driver discovery took roughly 100 seconds, and later driver staging took many minutes. Changing progress, block counters, and Panther logs distinguished work from a hang. Fixed short sleeps or a vanished panel were not reliable failure tests. |
| Installer USB had boot priority 1. | At the first installation reboot it returned to the account menu. Detaching the USB and booting the internal disk continued the existing installation. Returning to the menu was not evidence of a failed install. |
| Windows was `E:` during WinPE in these tests. | Discover the actual drive containing Windows and Panther logs; never assume `C:` during Setup. In this run the active log was `E:\$WINDOWS.~BT\Sources\Panther\setupact.log`. After normal Windows boot, the OS was `C:`. |
| `setuperr.log` contained three entries despite a successful desktop. | Preserve and interpret errors with the final result. The retained entries concerned MultiEdition-key cleanup, absent 2023 certificate in the VM DB, and system-disk detection. They were non-blocking in this test, not a generic allowlist of harmless errors. [Original log](../verification/local/exported/setuperr.log). |
| Shift+F10 opened a command window while OOBE retained or stole keyboard focus. | Inspect a screenshot, focus the command window's title bar, then type and verify the result. Sending a command successfully through QMP only proves delivery to QEMU. It does not prove the intended guest window executed it. |

Screenshot names are checkpoints, not assertions. For example, cloud `45-secureboot-state.png` and `46-secureboot-state.png` show an empty prompt because the command had not run. They are not Secure Boot proof. Use the final Home diagnostic export and screenshot instead. The cloud personal-use selection was verified in `55-personal-selected.png`; an earlier checkpoint had the other choice selected.

## Using the existing VM and QMP scripts

Run examples with Bash from a **fresh, isolated run root**, using the rebuild runbook's `.runs/<unique>/` layout with copied scripts/account sources, fresh `verification/` and `staging/`, and the required cached ISO/driver payloads. The scripts derive their base from their own location, so copied scripts use that run's directories. These commands operate disposable VM state. They do not write the physical USB.

[build-test-media.sh](../scripts/build-test-media.sh) creates `verification/test-usb.img` from staging using loop mounting, FAT32 and `rsync`. It refuses an existing image and uses `sudo -n` for loop and mount operations. [start-test-vm.sh](../scripts/start-test-vm.sh) accepts exactly `local` or `cloud`. First create new state in the isolated run root:

```bash
set -euo pipefail
# Fail if either test directory already exists; preserve previous test evidence.
test ! -e verification/local
test ! -e verification/cloud
mkdir -p verification
mkdir verification/local verification/cloud
mkdir verification/local/tpm verification/cloud/tpm
qemu-img create -f qcow2 verification/local/system.qcow2 80G
qemu-img create -f qcow2 verification/cloud/system.qcow2 80G
cp /usr/share/OVMF/OVMF_VARS_4M.ms.fd verification/local/vars.fd
cp /usr/share/OVMF/OVMF_VARS_4M.ms.fd verification/cloud/vars.fd

# Build the test image once using runbook step 4 before starting the VMs.
# Do not rerun the builder here: it correctly refuses an existing image.
test -f verification/test-usb.img
bash scripts/start-test-vm.sh local
bash scripts/start-test-vm.sh cloud
```

The launcher needs each test's `system.qcow2`, `vars.fd`, and `tpm/` directory already prepared. It does not create a blank disk, initialize firmware/TPM state, or reset a prior installation. The recorded test used 80 GB qcow2 disks and OVMF's Microsoft-key template. The large disposable images were deleted after evidence export; retained firmware/TPM state alone cannot resume those VMs. There is no generic VM initialization/reset or log-export helper in `scripts/`; the commands above are the explicit initialization procedure. Do not run them over the original evidence directories.

`verification/test-usb.img` is the pre-test candidate. It predates the completed test evidence and final checksum manifest; renaming it does not produce a finalized release. After testing, follow [Ready-to-flash image packaging](ready-to-flash-image.md) to build and verify a separate image from finalized staging.

The launcher uses KVM, q35/SMM, four vCPUs, 6 GiB RAM, OVMF Microsoft firmware, swtpm 2.0, a read-only USB test image and a writable disposable system disk. `local` has `-nic none`; `cloud` adds emulated Ethernet. Inspect those arguments before each run. No host internal disk belongs in an installation-test VM.

[qmp.py](../scripts/qmp.py) takes the socket path first, then `screenshot`, `hmp`, `execute`, `type`, `query-status`, or `quit`. Use `/usr/bin/python3`: that interpreter had Pillow installed, which the screenshot function requires. QMP sockets must be accessed by their owner or an appropriately privileged process. The tool sandbox required escalation for these socket connections; a permission-review delay was once mistaken for a guest stall. The helper itself has no socket receive timeout; a bounded `timeout` wrapper is useful for read-only diagnostics.

```bash
set -euo pipefail
# Inspect before sending keys. The screenshot directory must exist.
/usr/bin/python3 scripts/qmp.py verification/cloud/qmp.sock screenshot verification/cloud/current.png
/usr/bin/python3 scripts/qmp.py verification/cloud/qmp.sock query-status
timeout 15s /usr/bin/python3 scripts/qmp.py verification/cloud/qmp.sock execute '{"command":"query-blockstats"}'

# Example only after the account menu is visibly ready: choose Microsoft mode.
/usr/bin/python3 scripts/qmp.py verification/cloud/qmp.sock type $'2\n'
# Inspect the instruction/pause screen, then acknowledge it.
/usr/bin/python3 scripts/qmp.py verification/cloud/qmp.sock hmp 'sendkey ret'
```

`type` simulates US keyboard keystrokes; it is not clipboard paste. It supports ASCII alphanumerics and the punctuation map in the script, including pipe and newline. It does not accept every possible character (for example `%`, square brackets, and non-ASCII characters are absent). Use Bash `$'...'` quoting for intentional newlines and doubled backslashes for Windows paths. Never use this channel to type personal account secrets during validation. GUI focus, selected layout and key timing still matter.

At each screen, capture and inspect state before choosing the next action. `sendkey tab`, `shift-tab`, `spc`, `ret`, and `alt-n` worked where those controls were applicable, but tab order changed between pages. Wait in bounded intervals while the guest makes progress. Do not replay a sequence of key presses against an unseen transition or restart.

For mouse focus, `execute` can send QMP `input-send-event` messages. Absolute coordinates range from 0 to 32767. Calculate them from the latest screenshot; do not assume the old resolution. Separate button-down and button-up calls worked more reliably than sending both in the same event batch. For example, **only if the command title bar is at x=600, y=150 on a 1280×800 screenshot**, this focuses it:

```bash
set -euo pipefail
/usr/bin/python3 scripts/qmp.py verification/cloud/qmp.sock execute '{"command":"input-send-event","arguments":{"events":[{"type":"abs","data":{"axis":"x","value":15360}},{"type":"abs","data":{"axis":"y","value":6144}},{"type":"btn","data":{"down":true,"button":"left"}}]}}'
/usr/bin/python3 scripts/qmp.py verification/cloud/qmp.sock execute '{"command":"input-send-event","arguments":{"events":[{"type":"btn","data":{"down":false,"button":"left"}}]}}'
```

At the first **completed installation** reboot, detach the installer device. If the guest has already returned to the USB menu, reset it afterward to boot the internal disk:

```bash
set -euo pipefail
/usr/bin/python3 scripts/qmp.py verification/cloud/qmp.sock hmp 'device_del installer-usb'
/usr/bin/python3 scripts/qmp.py verification/cloud/qmp.sock execute '{"command":"query-block"}'
# Only after detachment is confirmed and the guest is at its reboot/menu stage:
/usr/bin/python3 scripts/qmp.py verification/cloud/qmp.sock hmp 'system_reset'
```

Use the corresponding `verification/local/qmp.sock` for the local VM. Device removal is asynchronous; verify it before resetting. Never reset while Setup is still copying files. Starting `start-test-vm.sh` again attaches the installer afresh, so it is not an internal-disk-only resume helper.

After the local desktop is visible, run the following in an elevated **guest PowerShell**, using the disposable account name actually created:

```powershell
Get-LocalUser MediaTest | Format-List Name, Enabled, PrincipalSource
Confirm-SecureBootUEFI
Get-WindowsDriver -Online | Select-Object Driver, OriginalFileName, ProviderName, ClassName, Version
```

Preserve screenshots and export text/driver inventories and Panther logs before deleting VM disks. The historical local test attached a separate VM-only log disk; `start-test-vm.sh` does not create it. The following explicit recipe creates a fresh 128 MiB FAT log image and attaches it to the running local VM as **removable** storage. Run from the isolated run root with permission to access that VM's QMP socket. It creates a regular file, never a physical-device target, and refuses an existing log image:

```python
from pathlib import Path
import json, shutil, subprocess

path = Path('verification/local/logs.img').resolve()
with path.open('xb') as f:
    f.truncate(128 * 1024**2)
mkfs = shutil.which('mkfs.vfat') or '/usr/sbin/mkfs.vfat'
subprocess.run([mkfs, '-F', '16', '-n', 'VMTESTLOGS', str(path)], check=True)
requests = [
    {'command': 'blockdev-add', 'arguments': {
        'driver': 'raw', 'node-name': 'logs',
        'file': {'driver': 'file', 'filename': str(path)}}},
    {'command': 'device_add', 'arguments': {
        'driver': 'usb-storage', 'drive': 'logs', 'id': 'logs-usb',
        'bus': 'usb.0', 'removable': True}},
]
for request in requests:
    subprocess.run(['/usr/bin/python3', 'scripts/qmp.py',
                    'verification/local/qmp.sock', 'execute',
                    json.dumps(request)], check=True)
```

The removable flag matters: the original fixed-disk presentation was not given
a drive letter. Confirm the label in elevated **guest PowerShell** before
writing, and substitute the actual disposable username if it is not MediaTest:

```powershell
Get-Volume | Format-Table DriveLetter, FileSystemLabel
$letter = (Get-Volume -FileSystemLabel VMTESTLOGS).DriveLetter
if (-not $letter) { throw 'VM log disk has no drive letter' }
Get-LocalUser MediaTest | Format-List Name,Enabled,PrincipalSource | Out-File ($letter + ':\account.txt')
Confirm-SecureBootUEFI | Out-File ($letter + ':\secureboot.txt')
Get-WindowsDriver -Online | Export-Csv ($letter + ':\drivers.csv') -NoTypeInformation
Copy-Item C:\Windows\Panther\setupact.log ($letter + ':\setupact.log')
Copy-Item C:\Windows\Panther\setuperr.log ($letter + ':\setuperr.log')
```

Use the console directly or adapt input to the QMP helper's supported characters;
the helper cannot type every PowerShell expression verbatim. After export
finishes, shut down this **local** VM from its still-focused guest console:

```bash
set -euo pipefail
/usr/bin/python3 scripts/qmp.py verification/local/qmp.sock type $'shutdown.exe /s /t 0\n'
```

Wait for the shutdown transition and confirm that this local VM has exited.
The separate cloud shutdown example below does not stop the local VM. Only
then read the regular image with mtools:

```bash
set -euo pipefail
test ! -S verification/local/qmp.sock
mkdir -p verification/local/exported
mcopy -i verification/local/logs.img '::*' verification/local/exported/
```

Review the exported values and driver counts. Do not delete the Windows/log
images until these files and the relevant screenshots have been preserved.

For graceful shutdown, open Shift+F10 during OOBE (or an elevated command prompt on the desktop), confirm focus, then send:

```bash
set -euo pipefail
/usr/bin/python3 scripts/qmp.py verification/cloud/qmp.sock hmp 'sendkey shift-f10'
# Wait, inspect, and focus the command window before the next command.
/usr/bin/python3 scripts/qmp.py verification/cloud/qmp.sock type $'shutdown /s /t 0\n'
```

Watch the guest transition and verify QEMU exits. In this run the QMP socket disappeared on clean shutdown. `qmp.py ... quit` exits QEMU directly; it is not a substitute for a graceful guest shutdown while preserving installation evidence.

## Revalidation procedure for a rebuild

1. Record the research date, Windows channel/edition/build, official ISO hash, download provenance, and the exact launcher/profile and boot-file hashes. Recheck current primary sources, but treat even recent claims as hypotheses until exercised against the actual ISO. Do not reuse a pass solely because the filename is unchanged.
2. Inspect the new boot WIM's relevant index and available binaries. Confirm `cmd`, `wpeinit`, `wpeutil`, and the chosen Setup binary. Validate answer-file XML and manually check for unintended disk, account, EULA, privacy or eligibility automation. Keep the default hardware checks separate from any explicitly selected compatibility helper.
3. Build the actual candidate test USB image and capture its complete file inventory and hashes in `verification/candidate-payload-sha256.json`, verifying that the files inside the image match the candidate staging tree. Keep this pre-test snapshot unchanged. Then prepare fresh virtual disks **and fresh firmware/TPM state** for each path. Archive prior evidence first. Verify the VM block graph has only the intended disposable storage and read-only installer. Verify local has no NIC and cloud has working networking.
4. Run Home/local through interactive account creation, password/appropriate recovery and privacy screens, independent disk boot, desktop, local identity and Secure Boot checks. Keep it offline throughout. Any bypass failure is a failure to investigate; do not silently replace the flow with a new console trick and retain the old pass claim.
5. Run Pro/Microsoft connected through personal-use setup to the empty Microsoft account-entry form. Allow the ordinary OOBE transition/update checks. If the GUI offers **Update later**, record whether it was selected and any restart. In this run the initial OOBE update occurred, and the later optional Windows update was deferred. Preserve both [the offered update](../verification/cloud/57-online-account-check.png) and [its confirmation](../verification/cloud/59-update-later.png).
6. Stop the cloud test at the empty Email/phone/Skype form with sign-in/create-account options visible. This proves the route is offered; it does not prove authentication or cloud desktop completion. Do not create or sign into an account just to extend a media test without a separate reason and authorization.
7. If claiming all editions support both choices, also test Pro/local and Home/Microsoft. If claiming online local creation, test it explicitly. Exercise malformed/missing marker, duplicate media, missing profile, invalid menu input, cancellation and restart recovery before claiming those branches are tested; the original run did not fully exercise them.
8. Export logs, driver inventories, screenshots and dated test notes; compare the full pre-test payload snapshot with finalized staging. Record real results from this run and enumerate every final difference. Permit only reviewed documentation/evidence and checksum-manifest differences without repeating functional tests. Driver additions are functional changes: record the difference and perform the affected validation separately. A new Setup binary/resource, boot file, profile, install image or relevant setup behavior requires repeating the affected account tests.
9. Build and verify the separate [ready-to-flash release image](ready-to-flash-image.md): check its exact payload inventory and hashes against frozen staging, its checksum manifest, filesystem and partition layout, then record the final image's byte size and SHA-256 and boot that image read-only to the menu. Release packaging does not rerun account tests. Physical flashing, device readback and a physical-USB boot check are subsequent steps when writing a USB. A physical Lenovo installation and real Wi-Fi/Ethernet test are still required to certify a particular laptop configuration.

## Bind account evidence to the final image

For a new run, the evidence chain is: **full pre-test candidate snapshot → observed account and driver results → finalized staging with explicitly recorded documentation/manifest-only differences → verified release-image contents → final image size and SHA-256**. Preserve `candidate-payload-sha256.json` alongside the test results. It covers the actual Setup executable and resources, every driver payload file, and the boot/profile files; the older eight-file record cannot substitute for it.

The account results retain their exact edition, network, date and endpoint limits. Driver evidence must identify its source/package manifest, source-to-staging all-file comparison and Windows acceptance results. A checksum match establishes that the release contains those bytes; it does not turn package acceptance into physical device testing or turn a sign-in form into successful authentication. Keep the historical baseline installation and later T15g acceptance scopes separate.

Completed screenshots, logs and documentation can be added after the installation tests. List their paths and hashes in the final comparison rather than rewriting the candidate snapshot to hide changes. With unchanged functional files and only those reviewed metadata differences, package from finalized staging and verify the resulting image. The outer image hash belongs in a sidecar or external release record, together with the payload-manifest digest and test scope. See the [packaging guide](ready-to-flash-image.md) for the executable procedure and required image checks.

## Finalization is not a test runner

[finalize-media.py](../scripts/finalize-media.py) is specific to the original build. It compares the staged files against the supplied account hash JSON (eight entries in the recorded run), checks that four evidence filenames exist, and reads a prior driver-validation JSON requiring `all_file_sha256_equal` and the snapshot-specific count **5,166**. It then hashes staging and writes `account_validation: passed` as a fixed string. It does not inspect screenshot contents, run a VM, authenticate an account, or recompute the source-to-staging driver comparison.

For a rebuild, the operator must perform and record the new tests, produce the real comparison results and matching candidate hashes, and review this snapshot-specific finalizer before using it. Copying the old screenshots/JSON into a new run can satisfy presence checks without proving any new behavior. Do not interpret successful execution of this script or release packaging as a fresh account-test pass. Once the actual tests and evidence are complete, refresh the staged evidence and full checksum manifest, freeze staging, then package and verify the release image against that manifest. Any later staged-file edit requires a refreshed manifest, a new release image and corresponding verification; changes to functional files also require the affected tests to repeat.

## How to weigh the dated sources

The strongest evidence here is the observed flow on the identified ISO, under the recorded network conditions. Official documentation describes interfaces but can lag the particular Setup binary. Current developer source explains an implementation but does not guarantee it survives an OOBE update. Community reports can reveal a sudden change, but need build, channel, date and reproduction details. Insider behavior is not automatically retail behavior. Date all claims and separate retrieval date from publication date and ISO creation date.

The September 18 research is preserved in [research-accounts/README.md](../research-accounts/README.md). No new web verification was performed for this September 19 documentation pass. In particular, “latest” in the original research means latest observed then.

| Source as reviewed September 18 | What it supported; limit |
| --- | --- |
| [Rufus 4.15 release](https://github.com/pbatard/rufus/releases/tag/v4.15), June 30, and [versioned source](https://raw.githubusercontent.com/pbatard/rufus/v4.15/src/wue.c) | `BypassNRO=1` implementation; automatic named-user creation is separate; empty product-key element rationale. Source inspection is corroboration, not a replacement for an installation test. |
| [Rufus FAQ](https://github.com/pbatard/rufus/wiki/FAQ#help-i-dont-see-the-option-to-bypass-the-need-for-a-microsoft-account-with-windows-11), page last edited July 17 | Account bypass depends on lack of internet connectivity. A mutable FAQ and its date cannot guarantee later retail behavior. |
| [Schneegans generator](https://schneegans.de/windows/unattend-generator/), reported commit `4037a44`, updated 1–2 days before research; [Users.cs](https://raw.githubusercontent.com/cschneegans/unattend-generator/master/modifier/Users.cs), [base template](https://raw.githubusercontent.com/cschneegans/unattend-generator/master/resource/autounattend.xml) | Interactive local mode removes precreated-user/AutoLogon settings and hides online-account screens; the template hides wireless setup. The `master` links are mutable: capture the new commit when rechecking. |
| [Microsoft HideOnlineAccountScreens](https://learn.microsoft.com/en-us/windows-hardware/customize/desktop/unattend/microsoft-windows-shell-setup-oobe-hideonlineaccountscreens), November 5, 2020 | Schema and default value. Too old to establish present OOBE behavior by itself. |
| [Microsoft Setup CLI](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/windows-setup-command-line-options?view=windows-11), [DynamicUpdate XML](https://learn.microsoft.com/en-us/windows-hardware/customize/desktop/unattend/microsoft-windows-setup-dynamicupdate), [Winpeshl.ini](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/winpeshlini-reference-launching-an-app-when-winpe-starts?view=windows-11) | `/Unattend`, XML update setting and sequential shell launch. `/DynamicUpdate` CLI was not listed as applicable to WinPE. `/DiagnosticPrompt` documentation disagreed with the actual media binary, as recorded above. |
| [Insider announcement March 28, 2025](https://blogs.windows.com/windows-insider/2025/03/28/announcing-windows-11-insider-preview-build-26200-5516-dev-channel/), [October 6, 2025](https://blogs.windows.com/windows-insider/2025/10/06/announcing-windows-11-insider-preview-build-26220-6772-dev-channel/) | Removal of bypass scripts/commands in preview builds motivated avoiding a dependence on OOBE console tricks. These announcements did not prove retail behavior. |
| [PC Gamer hands-on report](https://www.pcgamer.com/software/operating-systems/we-tested-the-simple-windows-11-account-bypass-and-it-works-just-no-one-tell-microsoft/), September 14, 2026 | Fresh community-derived “Learn more” bypass reproduced on a non-Insider install, without an exact stable ISO/build. It was deliberately not used for this media. |
| [Microsoft account conversion](https://support.microsoft.com/en-US/accounts-billing/manage/change-from-a-local-account-to-a-microsoft-account-in-windows), accessed September 18 | Switching account type after setup. This convenience does not substitute for providing both initial installation routes. |
