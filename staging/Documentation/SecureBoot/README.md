# Secure Boot inspection — 2026-09-18

The original Microsoft retail ISO's default `staging/efi/boot/bootx64.efi`, `staging/bootmgfw.efi`, and `staging/bootmgr.efi` each contain a signature chain through **Microsoft Windows Production PCA 2011**, issued by Microsoft Root Certificate Authority 2010. They are not signed by Windows UEFI CA 2023.

The complete source ISO matched Microsoft's live published SHA256 before extraction. For this inspection, the PE security directory was decoded, each PKCS7 certificate collection was extracted, and OpenSSL printed the certificates. This records signing certificates; it does not test a particular laptop's firmware DB/DBX or independently perform Authenticode validation. Raw PKCS7, readable certificates, file hashes, and dates are in this directory and `certificates-summary.json`.

The default bootx64 leaf certificate expired on June 17, 2026; its PCA2011 issuer expires October 19, 2026. **Expiration alone does not imply the image will be refused by UEFI.** Microsoft says a device without the new certificates continues starting normally after expiry, while losing access to new boot-security protections. Some devices need OEM firmware updates to complete the migration. See [Microsoft KB5079373](https://support.microsoft.com/en-us/servicing/os/secure-boot/2026/02/when-secure-boot-certificates-expire-on-windows-devices).

The separate, relevant failure condition is revocation. A machine with Microsoft Windows Production PCA 2011 placed in its Secure Boot DBX rejects boot managers signed under that authority. Trusting 2023 as well as 2011 does not itself revoke the older certificate. Secure Version Number restrictions can independently reject an older boot manager. See [Microsoft KB5025885](https://support.microsoft.com/en-gb/servicing/os/windows/2023/03/how-to-manage-the-windows-boot-manager-revocations-for-secure-boot-changes-associated-with-cve-2023).

## Optional 2023 material found inside this same ISO

Read-only extraction from install.wim image 1 produced:

- `efi-ex/bootmgfw_EX.efi`: signed through **Windows UEFI CA 2023**, SHA256 `d15b56f8800fa95efeeb63fb7b0891176fd40e447c10e44c3619e079487cd599`.
- `efi-ex/bootmgr_EX.efi`: still signed through **Microsoft Windows Production PCA 2011**. The EX suffix is not proof of the certificate used.

These inspection copies have not replaced any staged boot file. Microsoft provides `Make2023BootableMedia.ps1` plus the ADK to produce 2023 boot media, and requires a media source with current servicing updates. Such media requires firmware DB trust for Windows UEFI CA 2023. See [Microsoft KB5053484](https://support.microsoft.com/en-us/servicing/os/windows/2025/02/updating-windows-bootable-media-to-use-the-pca2023-signed-boot-manager).

## Lenovo implications

The default 2011 chain preserves compatibility with older firmware that still trusts PCA2011; it does not require enrolling 2023 merely to boot this USB. A fully migrated machine that has revoked PCA2011 needs suitable 2023 media instead. Actual machine state must be checked before promising universal Secure Boot compatibility.

Lenovo's [HT518129](https://support.lenovo.com/us/en/solutions/HT518129) lists minimum firmware versions that incorporate 2023 certificates into factory defaults. The English article's indexed regional copy provides these examples:

| L14/L15 variant | Minimum BIOS |
| --- | --- |
| Gen 1 Intel | R17ET41W, 1.24 |
| Gen 1 AMD | R19ET55W, 1.39 |
| Gen 2 Intel | R1JET69W, 1.69 |
| Gen 2 AMD | R1KET50W, 1.35 |
| Gen 3 Intel | R1XET53W, 1.35 |
| Gen 3 AMD | R1YET54W, 1.31 |

BIOS version alone is not proof of active DB contents. Lenovo describes separate activation through Microsoft's deployment mechanism or a factory-key operation. The latter can affect custom keys and existing OS bootability and was not performed. E485 was not found in the retrieved table; its migration support remains unverified. Confirm exact machine type and current vendor guidance before any firmware change. [Indexed English Lenovo table](https://support.lenovo.com/hr/en/solutions/HT518129).

No firmware changes, Secure Boot changes, USB writes, or changes to staging were made during this inspection.
