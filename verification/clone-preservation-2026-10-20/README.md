# Frozen build preservation audit

On October 20, 2026, the repository's frozen **25H2** build inputs and clone
instructions were audited without changing the Windows media, account profiles,
driver selection, historical test records or connected USB.

The [clone guide](../../docs/from-git-clone.md) documents restoration using the
existing official ISO and complete final driver payload. This avoids depending
on the continued availability of every original installer, including the E485
archive that was removed after extraction.

| Check | Result and evidence |
| --- | --- |
| Clean clone with no ignored ISO, driver binaries or release image | PASS; [clone audit](clone-audit.json) |
| Required tracked inputs and frozen source relationships | PASS; 235 files checked, 171 source entries, 170 distinct installers, 876 INF paths, 49 machine types; [source check](source-check.json) |
| Missing binary cache | Correctly failed; [expected missing-cache result](expected-missing-cache.json) |
| Existing ISO and full driver payload, read from the original workspace | PASS; ISO SHA-256 and all 5,166 driver files checked against the frozen reference; [cache result](preserved-cache-check.json) |
| Missing/untracked source, modified descriptor/checksum inventory, changed/extra/missing/symlink driver, wrong ISO | PASS; all 11 bounded tests; [test output](tests.txt) |
| Host command/firmware inspection | Build commands and firmware found; KVM access and loop-control visibility unavailable in this restricted environment; [host result](host-check.json) |
| Documentation syntax and references | Python parsed, Bash examples parsed, 39 local link targets/anchors checked, `git diff --check` passed |

The clone audit used a local candidate commit made from repository commit
`5e54e8e7b5c49e49023b59f7bcc5e16fecf559fa` plus the reviewed preservation changes,
then a separate `git clone --no-hardlinks` of that candidate. It did not copy
ignored working files into the clone. Its isolated candidate commit IDs are
test identities, not claims about a remote repository. [Reviewed file hashes](reviewed-files.sha256)
identify the six documentation/checker/test files tested in that clone.

The retained-cache check was run using:

```bash
python3 -B scripts/check-clone-inputs.py --preserved \
  --cache-root '/home/user/Documents/ChatGPT/MSW11 Installation Media' --json
```

After that check, host discovery was corrected to find `losetup` under
`/usr/sbin`, as used by the privileged build operations. The final candidate was
cloned again and its source check, all 11 tests, missing-cache test and host
inspection repeated. The cache-hashing code did not change. Both candidate
identities and that distinction are retained in `clone-audit.json`.

**No full media rebuild, VM boot, account flow, vendor-download replay, physical
USB operation or separate backup creation was performed in this audit.** The
restricted environment's device visibility was recorded without requesting
broader access. The earlier installation and boot evidence remains unchanged.

The source repository is reproducible only with its external binary inputs.
The current ISO and extracted driver payload were verified, not copied to a
second storage device. Keep a verified backup of them alongside a clone or Git
bundle, following the preservation guide. Do not equate a Git commit with a
backup of ignored files.
