# Official Windows 11 ISO acquisition

On 2026-09-18, the Microsoft page at <https://www.microsoft.com/en-us/software-download/windows11> displayed Windows 11 2025 Update, version 25H2. Selecting Windows 11 multi-edition ISO for x64 devices and English (United States) in the live browser generated the filename `Win11_25H2_English_x64_v2.iso` from `software.download.prss.microsoft.com`.

The live page verification table listed English 64-bit SHA256:

`768984706B909479417B2368438909440F2967FF05C6A9195ED2667254E465E3`

The download is 8,471,603,200 bytes. Its ISO headers date the media to March 7, 2026. This is the current retail image delivered by the official Microsoft page at the acquisition date. Installed Windows should receive updates after installation.

The official Microsoft page and public API refused shell HTTP requests (403), while the normal page flow in the browser succeeded. Fido source was inspected as reference only, never executed. The final image was downloaded with curl from the exact URL produced by the Microsoft browser flow, and its checksum is recorded separately in downloads/windows11-iso-provenance.json.
