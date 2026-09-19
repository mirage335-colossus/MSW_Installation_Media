# Offline local-account validation — 2026-09-18

Windows 11 Home, build 26200.8037, installed from the account-menu option 1 into a disposable 80 GB virtual disk. The VM had no network adapter. Region, keyboard, edition, license terms, and destination disk remained interactive. At the first restart the installer USB was removed and the internal virtual disk booted independently.

OOBE offered “Who’s going to use this device?” and a password prompt. A temporary MediaTest account was entered only in this VM; no username or password is embedded in the USB. Privacy choices remained interactive. The Windows desktop and Start menu appeared successfully (51-desktop-progress.png).

The tested boot WIM, split installation image, profiles, marker, and default EFI loader match the final media. The driver bundle present during installation comprised 159 packages before the separately verified T15g additions. This checks the setup/account flow; it does not test actual Lenovo hardware.

Desktop diagnostics confirmed `Get-LocalUser MediaTest` has `PrincipalSource: Local` and `Confirm-SecureBootUEFI` returned `True` (54-diagnostic-results.png).

The installed image contains 416 third-party driver entries, including 50 network entries after deduplication. The final T15g additions were not present in this VM. Setup retained three non-blocking error-log entries (MultiEdition-key cleanup; no 2023 certificate in the VM firmware DB; system-disk detection), with successful independent boot and desktop afterward. The VM was shut down normally and exported logs are retained under `exported/`.

The baseline contains 415 distinct INF SHA-256 values. Their per-class counts match all 415 Lenovo driver-store entries exactly; the 416th entry is Microsoft’s printer INF prnms009.inf. See driver-store-comparison.json.
