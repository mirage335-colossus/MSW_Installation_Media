# Test an installer image and the USB made from it

Use this guide to decide whether the installer is ready for the **specific use
you tested**. “Without significant errors” means no unresolved error preventing
that endpoint, and evidence explaining any accepted non-blocking findings.
It does not mean every Windows log must be empty.

The commands and evidence links follow the September 18 installation/USB tests
and September 19 release-image tests. This guide adds explicit acceptance rules
and repeat-test recipes; publishing these instructions does not perform a new
installation or certify additional hardware.

The standalone integrity recipe below was also executed against the existing
release image on September 19: [commands, results and scope](../verification/testing-guide-2026-09-19/README.md).

## Choose the claim and required tests

| Check | Required passing endpoint | What it establishes |
| --- | --- | --- |
| Image integrity | Correct complete-image hash/length; exact file inventory and hashes; valid partition/FAT geometry; successful filesystem check | The image contains the intended bytes and a readable filesystem. |
| Image boot | That exact image reaches the readable account-choice menu in a fresh UEFI VM; keyboard-driven shutdown works; image hash remains unchanged | The image boots under the recorded firmware configuration. |
| Setup and local account | Offline Home installation to a disposable disk, interactive choices, independent disk boot, local identity and desktop | The tested local-account installation path works. |
| Setup and Microsoft account | Connected Pro installation, independent disk boot, empty Microsoft sign-in form | The online account path is offered. Authentication/desktop is a separate endpoint. |
| Driver acceptance | Intended driver packages accepted by Windows; distinct additions and classes reconciled; required packages have no unresolved failure | Windows accepts the bundle; emulated hardware does not establish physical device function. |
| Written USB integrity | The particular USB matches the raw image, or matches the complete file-copy manifest; filesystem/partition checks pass | The write produced the intended media on that device. |
| Written USB boot | The verified physical USB reaches the menu under the recorded UEFI environment | That stick boots in that environment. A USB-backed VM is still not a Lenovo laptop. |
| Lenovo bootstrap usability | Intended laptop independently boots the installed desktop; input/storage work; Wi-Fi and Ethernet each provide internet separately | Bootstrap usability of that tested machine type, firmware/storage configuration and adapters. |

Use **PASS**, **FAIL**, **NOT RUN**, or **INCONCLUSIVE** for each new test. Record
reused results separately as **INHERITED**, with their original date, artifact
hashes, conditions and limits. Missing tools or unavailable hardware make a check
inconclusive/not run; they cannot produce a pass. A checksum error or a repeatable
boot failure fails that check. Do not flash an image with an unresolved integrity
failure or claim an untested endpoint.

For a new release, require image integrity/boot plus the relevant installation
and driver tests. Reuse earlier installation results only with documented evidence
that the tested functional files are unchanged; see the
[full candidate snapshot rules](ready-to-flash-image.md#bind-fresh-account-tests-to-the-complete-candidate).
Then require write verification for each USB. A claim about all Lenovo variants
also needs the relevant physical hardware tests; no VM-only result supplies them.
Start a new [test report](templates/test-report.md) rather than copying old pass fields.

## Record the artifact and environment before testing

Keep the image immutable and use a new evidence directory. Record the source
ISO/version/edition, release image SHA-256 and byte length, payload-manifest hash,
driver selection, script versions and whether installation evidence is new or
inherited. Record host/QEMU versions, firmware code and initial variable-file
hashes, Secure Boot/trust configuration, VM disk/network configuration and dates.
Use fresh writable OVMF variables, TPM state and disposable installation disks.
The historical installed VMs were removed; their screenshots are evidence, not
resumable test environments.

For standalone verification, retain this reference bundle beside the image:

```text
MSW11-Lenovo-x64.img
MSW11-Lenovo-x64.img.sha256
release-image.json
source-validation-ready.json
SHA256SUMS.source.txt
source-preflight.json
```

The builder already produces these files. Keep the installation/driver test
notes and boot evidence with the bundle too. The following example verifies the
existing `release/r3` artifact using a **new** `verification/t1` directory; change
those names for another artifact/run. All commands run from the repository root
as the ordinary user. Loop mounts need `sudo -n` and the
[documented Linux dependencies](runbook.md#2-prepare-the-host-and-an-isolated-working-directory).

```bash
set -euo pipefail
release_dir="$PWD/release/r3"
check_dir="$PWD/verification/t1"
image_path="$release_dir/MSW11-Lenovo-x64.img"
mkdir "$check_dir"
python3 - "$release_dir" <<'PY'
from pathlib import Path
import hashlib, json, stat, sys
root = Path(sys.argv[1])
for name in ('INCOMPLETE.txt', 'MSW11-Lenovo-x64.partial.img',
             'release-image.json.partial', 'MSW11-Lenovo-x64.img.sha256.partial'):
    if (root/name).exists() or (root/name).is_symlink():
        raise SystemExit('Incomplete packaging output: '+name)
for name in ('MSW11-Lenovo-x64.img', 'MSW11-Lenovo-x64.img.sha256',
             'release-image.json', 'source-validation-ready.json',
             'SHA256SUMS.source.txt', 'source-preflight.json'):
    if not stat.S_ISREG((root/name).lstat().st_mode):
        raise SystemExit('Need a regular, nonsymlink input: '+name)
report = json.loads((root/'release-image.json').read_text())
if report['status'] != 'verified' or (root/'MSW11-Lenovo-x64.img').stat().st_size != report['image_bytes']:
    raise SystemExit('Release status or image length differs')
expected_line = report['image_sha256']+'  MSW11-Lenovo-x64.img\n'
if (root/'MSW11-Lenovo-x64.img.sha256').read_text() != expected_line:
    raise SystemExit('Image checksum companion differs from release report')
for name, key in [('source-validation-ready.json', 'source_validation_ready_sha256'),
                  ('SHA256SUMS.source.txt', 'source_sha256_manifest_sha256')]:
    if hashlib.sha256((root/name).read_bytes()).hexdigest() != report[key]:
        raise SystemExit('Reference evidence changed: '+name)
print('Reference bundle and declared image length agree.')
PY
(cd "$release_dir" && sha256sum -c MSW11-Lenovo-x64.img.sha256) \
  > "$check_dir/image-sha256.txt" 2>&1
python3 scripts/verify-release-payload.py geometry --image "$image_path" \
  --report "$check_dir/geometry.json"
```

Use the expected checksum from the identified release; hashing an unknown image
and then treating its own newly calculated digest as the expected value does not
validate it. The `geometry` helper checks this project's fixed MBR/FAT32 layout,
including the documented 44-sector formatter tail. It accepts a regular image
file, not a USB block device. It is deliberately not a generic ISO checker.

Recheck the filesystem and complete payload through a read-only loop attachment:

```bash
set -euo pipefail
mount_path="$check_dir/image-mount"
mkdir "$mount_path"
image_loop=''
cleanup_image_check() {
  status=$?
  trap - EXIT
  set +e
  if mountpoint -q "$mount_path"; then sudo -n umount "$mount_path" || status=1; fi
  if test -n "$image_loop"; then
    if mountpoint -q "$mount_path"; then status=1
    else sudo -n losetup -d "$image_loop" || status=1; fi
  fi
  exit "$status"
}
trap cleanup_image_check EXIT
image_loop=$(sudo -n losetup --find --show --partscan --read-only --sector-size 512 "$image_path")
sudo -n losetup --list --json --output NAME,BACK-FILE,BACK-INO,OFFSET,SIZELIMIT,RO,LOG-SEC \
  "$image_loop" > "$check_dir/loop-read.json"
python3 scripts/verify-release-payload.py loop --device "$image_loop" --image "$image_path" \
  --metadata "$check_dir/loop-read.json" --read-only
for attempt in {1..50}; do
  test -b "${image_loop}p1" && break
  sleep 0.1
done
test -b "${image_loop}p1"
sudo -n fsck.vfat -n "${image_loop}p1" > "$check_dir/filesystem-check.txt" 2>&1
sudo -n mount -t vfat -o "ro,uid=$(id -u),gid=$(id -g),umask=022,utf8=1,nosuid,nodev,noexec" \
  "${image_loop}p1" "$mount_path"
python3 scripts/verify-release-payload.py payload --root "$mount_path" \
  --ready "$release_dir/source-validation-ready.json" \
  --manifest "$release_dir/SHA256SUMS.source.txt" \
  --reference-layout "$release_dir/source-preflight.json" \
  --report "$check_dir/payload-readback.json" > "$check_dir/payload-readback.txt" 2>&1
sudo -n umount "$mount_path"
sudo -n losetup -d "$image_loop"
image_loop=''
rmdir "$mount_path"
trap - EXIT
```

Require successful exit from every check and review the reports/logs. A list of
some successful checksums is insufficient. The helper checks the entire file set,
manifest itself, all file hashes and the reference directory layout, including
unlisted additions and unreadable paths. If `fsck` reports repairs are needed,
investigate/rebuild; do not silently repair the frozen image and retain its old
checksum or boot evidence. Do not invoke the helper's internal `release`
publication subcommand as if it independently re-ran these checks.

## Test actual boot behavior

Use the [exact release-image boot procedure](ready-to-flash-image.md#boot-the-exact-release-image-before-handing-it-off).
It starts QEMU paused, attaches the installer read-only, supplies fresh private
firmware variables, and attaches no network or installation destination. Before
resuming, inspect the graph and confirm that the image and firmware code are
read-only at every backing layer and that only the private variables are writable.
Record the graph, initial firmware hashes and launch command.

The minimum boot pass, matching the September 19 test, requires:

1. The **actual account-choice menu** appears with readable local/Microsoft,
   troubleshooting and shutdown entries. No firmware rejection, missing loader,
   crash, unexpected recovery screen or boot of another disk occurs.
2. Keyboard input reaches that menu and option 4 shuts the guest down normally.
   Wait for the VM process/socket to disappear as in the procedure.
3. The image still matches its complete-image SHA-256 after shutdown. Retain the
   final screenshot and checksum result, not just a “VM started” message.

A menu pass is not a Setup or desktop pass. For new launcher/profile changes,
also test blank/invalid menu input, option 3 followed by `exit`, each account
path's instructions and actual Setup launch, and cancellation/recovery behavior.
Use fresh VM starts for local and Microsoft branches, following the launcher's
instruction to reboot before switching profiles. Missing/duplicate markers or
missing profile/Setup-file tests require deliberate disposable test copies;
record their expected recovery messages and never modify the release to test them.
These broader recovery cases were not comprehensively exercised in the historical run.

### Recognize progress and collect a failure before resetting

While a VM is running, use its **actual** socket path, take screenshots and compare
block activity at sensible intervals. For the menu-only VM from the image guide:

```bash
set -euo pipefail
timeout 15s /usr/bin/python3 scripts/qmp.py "$smoke_dir/qmp.sock" query-status
timeout 15s /usr/bin/python3 scripts/qmp.py "$smoke_dir/qmp.sock" execute \
  '{"command":"query-block"}' > "$smoke_dir/current-blocks.txt"
timeout 15s /usr/bin/python3 scripts/qmp.py "$smoke_dir/qmp.sock" execute \
  '{"command":"query-blockstats"}' > "$smoke_dir/current-blockstats.txt"
/usr/bin/python3 scripts/qmp.py "$smoke_dir/qmp.sock" screenshot "$smoke_dir/current.png"
```

The helper prints Python-style text for these QMP results, not JSON. Host disk
activity shows progress but is not proof the desired guest operation completed.
The earlier Setup discovery took about 100 seconds, and driver staging took many
minutes. A blank/purple panel alone did not establish a hang. Record elapsed time,
screens, log growth and repeated state observations. If the chosen time budget
ends without the endpoint, mark it inconclusive or failed-to-reach-endpoint with
the reason; do not turn the absence of an error dialog into PASS.

On a failure, preserve a screenshot, phase, exact code/message and current logs
before shutdown/reset. Verify console focus before typing Shift+F10 diagnostics;
a command delivered to QEMU may have gone to the wrong window. A tool permission
failure or QMP timeout is a host-test issue until guest evidence establishes an
installer failure. `qmp.py ... quit` terminates QEMU directly; prefer guest shutdown
for a successful test and record forced termination when troubleshooting.

## Test installation, account choice and driver acceptance

Follow [account test initialization and evidence export](account-choice-and-testing.md#using-the-existing-vm-and-qmp-scripts)
and the [driver acceptance procedure](driver-maintenance.md). For tests of an
already packaged image, use a fresh isolated run root with copied `scripts/`,
copy that image to its `verification/test-usb.img` (the launcher's fixed path),
and verify the copy has the release image's SHA-256. **Do not rebuild or silently
substitute an earlier test image.** Then create new 80 GB guest disks, OVMF
variables and TPM directories as documented. Budget the runbook's free disk/RAM
requirements and use its short socket-safe paths.

Both paths must launch Setup and preserve interactive locale, edition, EULA and
destination-disk choices. Install only to the designated disposable/authorized
destination. Detach the installer after the first completed-install restart,
confirm detachment, and boot the installed disk independently. Returning to the
USB menu because it is first in boot order is different from an installed-OS boot
failure; record the distinction and verify the internal-disk continuation.

| Path | Pass criteria and evidence |
| --- | --- |
| Home/local, offline through desktop | User/password and applicable recovery/privacy screens work; desktop and Start menu are usable; `Get-LocalUser` shows `PrincipalSource=Local`; independently booted disk and Secure Boot result recorded. No Microsoft account is required under this offline procedure. |
| Pro/Microsoft, connected | Normal online OOBE, including any update/restart transitions, reaches the empty email/phone/Skype entry form with sign-in/create-account choices. No local-account path is forced. Stop there for the historical test endpoint. |
| Cloud authentication/desktop | Separate, explicitly scoped test using an authorized account; record it only if actually performed. It was not part of the recorded media tests. |
| Windows driver acceptance | Preserve PnPUtil/SetupAPI output and before/after driver inventories. Reconcile distinct INFs and class additions, already-present packages and dependencies. Do not equate every INF path with a distinct installed package or device binding. |

For a fresh driver union, include it before both installs. The historical full
installs used 159 packages/415 unique Lenovo INFs; the subsequent T15g check
accepted all 90 inputs (50 shared, 40 new) and increased the store from 416 to
456 entries, including Microsoft's printer INF. That separate acceptance test
did not repeat Setup with the entire final union. Keep that scope explicit.
Do not require a physical laptop to have exactly 456 driver-store entries:
its existing drivers, edition and updates may differ. Reconcile the packages
under test and their actual bound devices instead of using that historical total
as a universal acceptance threshold.

## Assess errors with context

Start with `setuperr.log`, then inspect matching timestamps and surrounding
operations in `setupact.log`; use driver/servicing logs for the relevant phase.
Early WinPE logs are temporary, so export them before reboot. Microsoft's
[deployment log reference](https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/deployment-troubleshooting-and-log-files?view=windows-11)
describes these phase-dependent locations; verify which files exist in the exact
image rather than assuming every documented path is present.

| Phase | Logs/evidence to inspect |
| --- | --- |
| Early WinPE/Setup | `X:\Windows\Panther\` when present; launcher message/exit code; screenshot. |
| Setup on the destination | `<target>:\$WINDOWS.~BT\Sources\Panther\setupact.log` and `setuperr.log`; the original target was `E:` in WinPE. |
| Installed Windows/OOBE | `%windir%\Panther\setupact.log`, `setuperr.log` and the `UnattendGC` subdirectory where present. |
| Driver import/binding | `%windir%\INF\setupapi.offline.log` / `setupapi.dev.log`, plus the actual PnPUtil transcript. |
| Manual bootstrap helper | `%SystemRoot%\Temp\Lenovo-bootstrap-drivers.log`. |
| Servicing | `%windir%\Logs\DISM\dism.log` and `%windir%\Logs\CBS\CBS.log` when the failed operation points there. |

Discover WinPE drive letters with **read-only** DiskPart commands:

```text
diskpart
list volume
exit
```

Do not use `clean`, `format`, or partition changes as log-discovery steps. From an
elevated **installed guest PowerShell** console, these inspect the tested endpoint:

```powershell
Get-LocalUser MediaTest | Format-List Name,Enabled,PrincipalSource
Confirm-SecureBootUEFI
Get-WindowsDriver -Online
pnputil /enum-devices /problem /deviceids
Get-Content C:\Windows\Panther\setupact.log -Tail 80
```

Substitute the actual disposable username. Export the full relevant logs and
inventories using the account guide, not only the last 80 lines. Use the guest
console for PowerShell syntax the QMP typing helper cannot represent. PnPUtil
distinguishes adding to the store from installing on matching devices; see its
[command reference](https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/pnputil-command-syntax).
Device-installation errors can be correlated with the
[SetupAPI device log](https://learn.microsoft.com/en-us/windows-hardware/drivers/install/setupapi-device-installation-log-entries).
Check the exact build's help when using a newer diagnostic flag.

Classify each finding with phase/time, exact message/code, surrounding context,
recovery/fallback, final endpoint and a reasoned disposition. Examples from the
recorded local installation:

| Finding | Why it did not block that run |
| --- | --- |
| MultiEdition-key cleanup error | The selected Home edition continued through licensing and installation. |
| 2023 certificate absent from firmware DB | `setupact.log` records the fallback away from EX binaries, followed by successful boot-file/boot-entry updates; independent boot and `SecureBoot=True` corroborated it. |
| “System disks found” logged at error level | Surrounding operations completed WinRE installation and identified the system disk; independent boot and desktop succeeded. |

See the [three original error entries](../verification/local/exported/setuperr.log),
[surrounding activity log](../verification/local/exported/setupact.log), and
[local test note](../verification/local/test-notes.md). These are dated dispositions,
**not an ignore list**. A new trust/revocation failure, unexplained storage error,
driver rejection, crash, rollback, repeated OOBE loop, blocked account choice or
failed independent boot remains unresolved until investigated. The old
`/DiagnosticPrompt Enable` exit 31, for example, was a real failure that required
changing the launcher and restarting the tests.

## Verify each written USB

First record that job's exact by-id path, serial, model, USB/removable identity,
byte capacity, logical sector size and partition topology. Recheck identity after
reconnection; `/dev/sda` or “64 GB” alone is insufficient. Wait for the writer's
flush/completion, keep the selected USB and its children unmounted for block
checks, and prevent desktop automount during verification.

Use the verification method that matches how the stick was made:

| Write method | Required readback |
| --- | --- |
| Raw `.img` flash | Use the [identity-checked raw-write/readback procedure](ready-to-flash-image.md#hand-off-and-flash-the-image). `cmp --bytes=<image length>` must exit zero after flushing, comparing the entire image prefix on that exact device. Save command, exit status, image hash, target identity and date; silence alone is not a recorded result. |
| Direct staging-to-USB file copy | Use [runbook steps 8–9](runbook.md#8-optionally-select-the-physical-target-write-and-verify). Require every payload hash, the manifest's own hash, a successful read-only FAT check and the intended partition table. A different MBR/FAT ID means raw-image hashes need not match. |

The original September 18 USB was made by **direct file copy**. The September 19
`release/r3` raw image was created and VM-booted later; it was not raw-flashed to
that stick. Therefore a raw comparison between those two artifacts is not the
historical USB's acceptance test. Their payload hashes are the relevant comparison.

For filesystem inspection after either method, run `fsck.vfat -n` only on the
identified **unmounted partition**, record `fdisk -l`/`sfdisk --json` geometry,
and optionally repeat the payload helper on a read-only mount using the same
reference bundle as above. Use explicit user/group/mask options. Save the full
reports and unmount afterward. The `geometry` helper is for regular image files;
do not point it at the USB. A raw-prefix match already binds its MBR/BPB bytes to
the verified image; still inspect larger-device tail signatures/partition topology.

The [existing physical-USB VM launcher](../scripts/start-physical-usb-test.sh)
provides the historical read-only USB-backed menu test for the direct-copy
workflow. It is pinned to the original Kingston serial and exact capacity,
requires a fresh `verification/physical-boot` directory and these three files:

```text
verification/usb-readback-sha256.txt
verification/usb-filesystem-check.txt
verification/usb-final-partition-table.txt
```

Those must be genuine evidence from the **same current write job**. The script
only checks that the files are nonempty; that is not proof of their contents or
freshness. Never copy old logs to bypass the prerequisite. Run in the isolated
job directory and follow the runbook's identity review, menu capture and shutdown
steps. It is not a generic raw-flash verifier and the raw `dd/cmp` recipe does
not automatically produce its required evidence.

For a raw-flashed USB, the verified image VM boot plus exact physical readback
establishes that its intended boot bytes were written. Complete the actual-device
check by selecting that USB from the intended laptop's UEFI boot menu, recording
the menu/input/shutdown result. Keep installation separate until a destination is
explicitly designated. Record model/type, BIOS version, Secure Boot setting/trust
context, USB identity and any firmware rejection. A QEMU pass does not override a
failure on the target Lenovo; consult the [Secure Boot guide](source-media-and-secure-boot.md).

Perform immutable byte comparison **before** allowing a physical machine to boot
the writable USB. Firmware/Windows may later change filesystem metadata; a later
whole-device mismatch needs investigation and a payload check, not an automatic
conclusion that an installer file was corrupted. Record the timing of each check.

## Check real Lenovo bootstrap usability

These are required new hardware tests before claiming a particular configuration
works. They were not performed by the recorded QEMU tests. Use the
[machine-type and hardware-ID coverage map](driver-maintenance.md#covered-families-and-machine-types),
not the preparation host's one network adapter, to select representative Intel,
Realtek, Qualcomm and MediaTek variants across E485/L14/L15 and T15g Gen 1.

For each tested machine, record its type, BIOS, CPU/platform, storage mode and
controller ID, Wi-Fi/Ethernet hardware IDs and driver versions. Confirm Setup
sees the intended internal disk, keyboard/touchpad work, the installed disk boots
without USB, and the basic desktop is usable. Record any manual **Load Driver**
or bootstrap-helper step needed, including the exact package. On T15g, exercise
the actual configured Intel RST/storage mode; acceptance in a VM does not prove
RAID access. E485's unsupported CPU/Windows 10 driver status remains explicit.
Record bound driver versions and initial failures before Windows Update or a
manual recovery step changes them; otherwise later downloads can mask a gap in
the shipped bootstrap bundle.

Test **Wi-Fi and Ethernet separately**, with the other connection disconnected
and no alternate internet route. For each: establish link/association, obtain a
usable address/default route, resolve a public name, open an HTTPS site and
record the result. A link light, a successful ping, an adapter shown in Device
Manager or reaching the cloud form over emulated Ethernet alone is insufficient.
Repeat after a normal reboot before calling the bootstrap configuration usable.
Record captive-portal, network-service or access-point failures separately from
adapter/driver failures, resolving them before the internet endpoint can pass.

Useful read-only commands in the installed guest include:

```powershell
Get-NetAdapter
Get-NetIPConfiguration
ipconfig /all
netsh wlan show interfaces
Resolve-DnsName www.microsoft.com
Test-NetConnection www.microsoft.com -Port 443 -InformationLevel Detailed
pnputil /enum-devices /problem /deviceids
```

Also open the HTTPS page in a browser; TCP port reachability alone does not prove
an HTTP request succeeded. Retain the relevant adapter/problem-device evidence,
including the connection result's interface and source address to confirm the
intended adapter carried the test. Exclude passwords and wireless key exports.
Review unknown/problem devices against
the bootstrap requirements: an unresolved storage, input, Wi-Fi or Ethernet
problem blocks that claim. An excluded GPU/audio/WWAN feature needs a recorded
scope note; its absence is not proof the included bootstrap drivers failed.

## Close the test and preserve the evidence

Fill in the [test report template](templates/test-report.md) with actual outcomes.
Every PASS needs artifact identity, conditions, endpoint evidence and disposition
of significant findings. Keep new/inherited results visibly separate, including
the cloud sign-in-versus-authentication distinction and real hardware limits.
Preserve screenshots, complete relevant logs, inventories, readback reports,
source/final hashes and exact commands before deleting disposable VM disks.
Confirm all VMs have stopped and image loops/USB mounts are detached. Keep the
verified deliverable and compact evidence; do not overwrite historical results.

Reference passes are in the [September 18 completion report](../verification/FINAL-REPORT.md)
and [September 19 image validation](../verification/release-image-2026-09-19/README.md).
Use them as dated examples, never as substitutes for evidence from a changed
image, a newly written USB or a different laptop configuration.
