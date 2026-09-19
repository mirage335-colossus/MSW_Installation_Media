# T15g driver acceptance validation

The existing Windows 11 Home local-account VM booted its installed OS directly, with Secure Boot enabled and no network. A separate read-only virtual removable disk supplied the 12 additional T15g packages. An elevated `pnputil /add-driver <input>\Drivers\*.inf /subdirs` accepted all 90 INF packages with exit code 0. No `/install` or force option was used.

Fifty INF packages were already present from the baseline media. Forty new entries were added, increasing the third-party driver store from 416 to 456 entries. The added class counts match the 40 distinct new source INF hashes exactly. Thunderbolt host INFs automatically import three dependent packages each; subsequent already-present messages for these same dependencies do not represent additional distinct inputs. `validation-summary.json`, the exported PnPUtil transcript, before/after inventories, setup API logs, and `15-validation-result.png` preserve the evidence.

The VM shut down normally after export. The physical USB and frozen staging tree were not modified. This verifies Windows signature and payload acceptance, not actual T15g hardware functionality or BIOS/storage configurations. The VM's previously recorded local-account and installation-flow test remains separate.
