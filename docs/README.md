# Rebuilding and maintaining this installer

This repository records an installation-media build completed on **2026-09-18**.
The maintenance documentation was consolidated on **2026-09-19**. Its dated
observations describe that run; they are not a claim that today's OOBE or driver
catalogs behave identically. The existing USB and its recorded payload remain a
separate, verified artifact.

| Need | Start here |
| --- | --- |
| Perform a rebuild, test it, and write a USB | [Runbook](runbook.md) |
| Create a ready-to-flash `.img`, verify it, and hand it off | [Release image build and flashing](ready-to-flash-image.md) |
| Decide whether an image/USB passed boot, installation and usability testing | [Testing and acceptance](testing-and-acceptance.md), [blank test report](templates/test-report.md) |
| Preserve a usable local/Microsoft account choice | [Account design and testing](account-choice-and-testing.md) |
| Cover broad E485/L14/L15 factory hardware, plus T15g Gen 1 | [Driver maintenance](driver-maintenance.md) |
| Obtain and verify Microsoft media; understand Secure Boot | [Source media and Secure Boot](source-media-and-secure-boot.md) |
| Avoid the mistakes and delays found during the first run | [Lessons and troubleshooting](lessons-learned.md) |
| Operate the finished USB | [Installation guide](../README.md) |
| Inspect what actually passed | [Completion report](../verification/FINAL-REPORT.md), [machine-readable result](../verification/FINAL-RESULT.json) |
| Inspect the final image builder's integration and boot tests | [September 19 packaging validation](../verification/release-image-2026-09-19/README.md) |

## Repository map

- `scripts/`: media construction, isolated test-image/VM launch, QMP control,
  final hashing, guarded physical writing, and read-only USB boot verification.
- `research-accounts/`: the authoritative custom launcher and answer-file
  sources, dated research, and optional E485 compatibility helper.
- `research-drivers/`: versioned model catalogs, package descriptors, source
  manifests, selection audits, extraction scripts, and driver coverage maps.
- `downloads/`: versioned ISO provenance and checksum alongside an **ignored**
  local ISO, when available. Microsoft download URLs can expire.
- `research/iso-acquisition/`: dated acquisition notes, not a permanent download
  API or a redistribution source.
- `staging/`: the finished USB tree. Custom files and documentation are tracked;
  Microsoft and Lenovo payload binaries are ignored. Do not treat its preserved
  validation files as evidence for a different build.
- `verification/`: historical logs, screenshots, inventories, hashes, and test
  code. VM disks were deliberately removed after verification; they are not
  needed to inspect the results, but must be recreated for new tests.
- `.runs/`: ignored, isolated workspaces for future runs. Promote reviewed source
  changes and compact new evidence deliberately; do not add the whole directory.
- `release/`: ignored raw/compressed image products and local packaging outputs.
  Keep the image with its checksum and report; promote compact reviewed evidence
  into a dated `verification/` location for Git.

A Git clone therefore contains the recipes and evidence, **not a complete USB
image or preinstalled Windows VM**. Recover/download the large inputs through
the runbook. Never add Windows media, vendor installers, mounted disk trees,
mutable TPM state, or test account credentials to Git. Keep relevant exported
logs and screenshots after checking that they contain no real account secrets.

The minimum tested outcomes are a Home/local desktop while offline and a
Pro/Microsoft sign-in form while online. Authentication, every edition/account
combination, and actual laptop device operation are separate tests. Broad
manufacturer driver coverage must be evaluated by machine type and hardware ID,
not inferred from the network adapter in the computer running this repository.
