# Installer image / USB test report

Copy this template into a new evidence directory and adjust relative links for its location.
Follow [Testing and acceptance](../testing-and-acceptance.md).
Every result starts **NOT RUN**. Change a result only after reviewing its evidence.
Use **PASS**, **FAIL**, **INCONCLUSIVE**, or **NOT RUN** for newly performed tests.
Record inherited observations separately; inheritance is not a fresh PASS.
Replace `*_LINK` placeholders with reviewed Markdown links. Do not include credentials.

## Run and artifact identity

| Field | Value |
| --- | --- |
| Report ID / operator / review date | `[fill in]` |
| Test start / end, UTC and local timezone | `[fill in]` |
| Artifact kind and path: candidate image, final image, or physical USB | `[fill in]` |
| Build source commit / local changes / run directory | `[fill in]` |
| Windows edition, architecture, language, version and actual build | `[fill in]` |
| Source ISO filename / official URL / retrieval date | `[fill in]` |
| Official ISO SHA-256 / measured ISO SHA-256 / provenance | `[fill in]` / `SOURCE_PROVENANCE_LINK` |
| Final raw-image logical byte size / SHA-256 / checksum sidecar | `[fill in]` / `IMAGE_CHECKSUM_LINK` |
| Payload manifest SHA-256 / file count / total payload bytes | `[fill in]` / `PAYLOAD_MANIFEST_LINK` |
| Full pre-test candidate snapshot / final comparison | `CANDIDATE_HASHES_LINK` / `CANDIDATE_COMPARISON_LINK` |
| Driver source manifest / all-file staging comparison / package and INF counts | `DRIVER_MANIFEST_LINK` / `DRIVER_COMPARISON_LINK` / `[fill in]` |
| Explicit documentation/evidence/manifest differences after installation tests | `[list paths and hashes, or none]` |
| Functional payload changes after tests and required retesting | `[fill in; do not replace the original candidate snapshot]` |

## Environment and isolation

| Field | Value |
| --- | --- |
| VM or actual laptop; machine type, model, CPU and relevant storage configuration | `[fill in]` |
| VM launcher/version/configuration and preboot block-graph evidence | `[fill in]` / `BLOCK_GRAPH_LINK` |
| Firmware/BIOS version; UEFI or legacy mode; firmware-state provenance | `[fill in]` |
| Secure Boot and TPM configuration; measured guest state and evidence | `NOT RUN` / `FIRMWARE_EVIDENCE_LINK` |
| Installation destination identity / capacity / disposable-data authorization | `[fill in]` |
| Physical USB model / serial / by-id path / exact byte capacity, if applicable | `[fill in]` |
| Physical target identity, unmounted children and write/read-only mode checks | `NOT RUN` / `DEVICE_IDENTITY_LINK` |
| Network conditions for each test; NIC model/driver; disconnected adapters | `[fill in]` |
| Account choice, edition, test-only username if used, and selected setup options | `[fill in; no passwords, tokens or personal account data]` |
| Online OOBE updates, optional update deferral, restarts and measured build changes | `NOT RUN` / `[record observed sequence]` |

## Newly performed acceptance gates

| Gate and required observation | New result | Evidence / measured outcome |
| --- | --- | --- |
| Exact payload inventory and every checksum, including manifest itself | NOT RUN | `INTEGRITY_LINK` |
| Raw-image size, partition layout and read-only filesystem check | NOT RUN | `GEOMETRY_FILESYSTEM_LINK` |
| Exact final image boots read-only to account menu; no destination attached | NOT RUN | `IMAGE_BOOT_LINK` |
| Menu/input usable; selected path launches Setup without unsupported-option or answer-file error | NOT RUN | `MENU_SETUP_LINK` |
| Edition, locale, EULA and destination selection remain interactive | NOT RUN | `SETUP_CONTROLS_LINK` |
| Installation completes and internal disk boots independently after installer removal | NOT RUN | `INDEPENDENT_BOOT_LINK` |
| Home/local while offline: user/password/privacy flow and usable desktop | NOT RUN | `LOCAL_DESKTOP_LINK` |
| Local identity reports PrincipalSource=Local; Secure Boot state recorded | NOT RUN | `LOCAL_IDENTITY_LINK` |
| Pro/Microsoft while connected: empty sign-in form; stop before credentials | NOT RUN | `MICROSOFT_FORM_LINK` |
| Expected driver packages accepted; exit codes and distinct store additions reconciled | NOT RUN | `DRIVER_ACCEPTANCE_LINK` |
| Reviewed Setup/driver errors; no unresolved error preventing the tested endpoint | NOT RUN | `ERROR_REVIEW_LINK` |
| Graceful shutdown; final image checksum unchanged after read-only boot test | NOT RUN | `SHUTDOWN_CHECKSUM_LINK` |
| Physical USB write, flush, exact readback, manifest and filesystem verification | NOT RUN | `USB_READBACK_LINK` |
| Actual written USB boots to menu; specify VM or physical laptop and firmware | NOT RUN | `PHYSICAL_USB_BOOT_LINK` |
| Actual Lenovo: disk visible, installation and independent desktop/input usable | NOT RUN | `LENOVO_DESKTOP_LINK` |
| Actual Lenovo Wi-Fi: association, addressing, DNS and HTTPS; Ethernet disconnected | NOT RUN | `WIFI_LINK` |
| Actual Lenovo Ethernet: link, addressing, DNS and HTTPS; Wi-Fi disconnected | NOT RUN | `ETHERNET_LINK` |
| Other edition/account combinations, recovery branches or additional requested tests | NOT RUN | `[name each additional case separately]` |

## Inherited observations — not newly executed

| Prior report/date and exact result scope | Artifact/hash relationship | Changes and justification for reuse | New execution status |
| --- | --- | --- | --- |
| `PRIOR_REPORT_LINK` / `[fill in]` | `[full snapshot, limited hashes, or other evidence]` | `[fill in; enumerate gaps and functional changes]` | NOT RUN |

Do not upgrade limited historical hashes into a full-payload claim. Separate baseline installation from later driver acceptance, and menu boot from full installation.

## Significant errors and disposition

An empty log is not the acceptance criterion. Review errors against the required endpoint and retain context and recovery evidence; unresolved findings cannot become PASS.

| Phase/time | Exact message/code and source log | Surrounding context | Recovery/fallback and evidence | Outcome / remaining impact | Disposition / reviewer |
| --- | --- | --- | --- | --- | --- |
| `[fill in]` | `ERROR_LOG_LINK` | `[fill in]` | `RECOVERY_EVIDENCE_LINK` | `[fill in]` | NOT RUN |

For each reviewed finding choose blocking, non-blocking for this run, or unresolved, and explain why. Do not carry forward an old ignore list. Record suspected stalls with elapsed time, screenshots, disk/log progress and the eventual outcome.

## Evidence index

| Evidence group | Links / hashes |
| --- | --- |
| Menus, Setup controls, account endpoints and desktop screenshots | `SCREENSHOTS_LINK` |
| Setup/Panther logs and error-context review | `SETUP_LOGS_LINK` / `ERROR_REVIEW_LINK` |
| Account/Secure Boot exports; driver-store inventory; PnPUtil/SetupAPI logs | `GUEST_EXPORTS_LINK` |
| Input provenance, candidate/final manifests, release report and image hash | `HASH_PROVENANCE_LINK` |
| Physical identity, write/readback logs and boot configuration | `PHYSICAL_EVIDENCE_LINK` |

## Final disposition and exact scope

- **Overall disposition: NOT RUN.** `[reviewer, date, and reason when completed]`
- **Newly established scope:** NOT RUN. `[artifact hash, environment, edition/account/network conditions and exact endpoints]`
- **Inherited scope only:** `[prior reports and unchanged-byte evidence; not fresh passes]`
- **Unresolved findings / omitted checks:** `[list every affected gate and next action]`
- **Limits:** `[explicitly state untested authentication, account combinations, actual Lenovo/storage/Wi-Fi/Ethernet, firmware trust, and optional components as applicable]`
- **Handoff artifact and evidence:** `[image/USB identity, final hash, report links; distinguish packaged image from physically written USB]`
- **Retest triggers:** `[functional changes, new ISO/build/OOBE behavior, changed drivers/firmware, and any remaining conditions]`
