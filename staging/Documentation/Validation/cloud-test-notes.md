# Cloud-account verification — passed to sign-in form

Date: 2026-09-18. Target: isolated QEMU VM `MSW11-cloud-verification`, 80 GB disposable virtual disk, read-only prepared USB test image, emulated Ethernet. No host disks or user-specific credentials were used.

Observed results:

- Initial `sources/setup.exe /DiagnosticPrompt Enable` invocation exited with code 31. The parent removed the unsupported flag, rebuilt the boot image, and restarted both tests. The final tested launcher uses `/unattend:` only.
- Built-in menu and marker reading worked; selected menu option 2, Microsoft account. Setup accepted `profiles/microsoft.xml`.
- Language/locale/keyboard, Windows edition, EULA acceptance, and target disk selection remained interactive. Windows 11 Pro was installed to the empty 80 GB test disk.
- Installation completed, including files, features, updates, and driver staging. The large driver collection caused long but progressing setup phases.
- Detached installer USB after the first installation reboot, then booted Windows independently from its internal virtual disk.
- OOBE accepted US region and keyboard, skipped second keyboard, performed an online update/restart, skipped optional device name, and offered both personal-use and work/school choices. Personal use was selected.
- The later optional Windows-update carousel offered Update later; this was selected and confirmed, triggering its advertised restart.
- Reached “Unlock your Microsoft experience”, then “Let's add your Microsoft account” with the empty Email, phone, or Skype field, Create one, and Sign-in options. Final proof: `63-microsoft-signin.png`. Test stopped at that screen; no account information was entered.
- Guest command prompt reported initial Windows build 10.0.26200.8037. No unsupported OOBE bypass command was used in this cloud path.

Scope and limits:

This verifies that the Pro/cloud media path reaches Microsoft's connected account-entry form. Authentication, cloud-account desktop completion, physical Lenovo hardware, Wi-Fi, and Ethernet drivers were not tested by this VM run. The other VM independently passed Home/offline local-account creation through desktop and confirmed PrincipalSource=Local and Secure Boot=True. Final T15g driver additions are separate from the unchanged account launcher/profiles exercised here.
