# Maintaining the Lenovo bootstrap drivers

This guide describes the driver collection retrieved on **September 18, 2026**, the decisions behind it, and how to reproduce or refresh it. It covers driver preparation and acceptance testing; use the [runbook](runbook.md) for account setup and assembly, then the [release-image guide](ready-to-flash-image.md) to produce a verified `.img` for flashing.

Use the [physical bootstrap checks](testing-and-acceptance.md#check-real-lenovo-bootstrap-usability)
to test actual storage, input, Wi-Fi and Ethernet operation and record findings
separately from package-store acceptance.

The finished collection contains **171 source-package directories, 876 INF paths, 73 network INF paths, 5,166 files, and 5,844,200,528 bytes (5.44 GiB)**. It provides bootstrap coverage: installation storage, a basic desktop, input, and Wi-Fi/Ethernet. GPU acceleration, audio, and optional hardware features can be completed through Windows Update or Lenovo's model-specific update tools after networking works. Package presence and a successful virtual-machine import do not establish that every physical laptop configuration works.

All shell examples start in the repository root. Use an isolated `.runs/<unique>/` workspace for rebuilds. The research scripts use paths relative to their own location and overwrite named JSON reports; they are not safe to run indiscriminately over the historical evidence or a frozen release staging tree.

## Covered families and machine types

The selection covers the following **49 machine types**. The type-to-package mapping, including each model's network alternatives, is in [model-coverage.tsv](../research-drivers/model-coverage.tsv). A shared SCCM archive can also name other products; that does not extend this collection's claimed coverage to those products.

| Family | Intel machine types | AMD machine types |
| --- | --- | --- |
| ThinkPad E485 | — | 20KU |
| ThinkPad T15g Gen 1 | 20UR, 20US | — |
| ThinkPad L14 Gen 1 | 20U1, 20U2 | 20U5, 20U6 |
| ThinkPad L15 Gen 1 | 20U3, 20U4 | 20U7, 20U8 |
| ThinkPad L14 Gen 2 | 20X1, 20X2 | 20X5, 20X6 |
| ThinkPad L15 Gen 2 | 20X3, 20X4 | 20X7, 20X8 |
| ThinkPad L14 Gen 3 | 21C1, 21C2 | 21C5, 21C6 |
| ThinkPad L15 Gen 3 | 21C3, 21C4 | 21C7, 21C8 |
| ThinkPad L14 Gen 4 | 21H1, 21H2 | 21H5, 21H6 |
| ThinkPad L15 Gen 4 | 21H3, 21H4 | 21H7, 21H8 |
| ThinkPad L14 Gen 5 | 21L1, 21L2 | 21L5, 21L6 |
| ThinkPad L14 Gen 6 | 21S6, 21S7 | 21S8, 21S9, 21SE, 21SF |
| ThinkPad L14 Gen 7 | 21X2, 21X3 | 21X6, 21X7 |

L14 Gen 6 has two AMD platform groups. L14P is a separate product and was excluded. L16, E585, P15, and P17 appear in some shared archive names, but were not independently selected as target families.

Factory network alternatives matter. Preserve Intel, Realtek, Qualcomm, and MediaTek WLAN packages found in the relevant catalogs, plus Ethernet packages, even when the laptop used to prepare the media has only one adapter. Its observed Qualcomm QCNFA765 `PCI\VEN_17CB&DEV_1103&SUBSYS_E0BE17AA` and Realtek Ethernet `PCI\VEN_10EC&DEV_8168&SUBSYS_509117AA` were useful sanity checks, not the selection boundary. Replacement cards require their own hardware-ID check.

The [T15g Gen 1 specification](https://psref.lenovo.com/syspool/Sys/PDF/ThinkPad/ThinkPad_T15g_Gen_1/ThinkPad_T15g_Gen_1_Spec.html) matches the requested i7-10750H / RTX 2070 SUPER configuration. Its factory networking is Intel AX201 Wi-Fi and I219-LM or I219-V Ethernet. The live catalogs for **both** 20UR and 20US were checked. GPU packages were intentionally excluded from this bootstrap collection.

## Sources, dates, and the integrity chain

The source entry points are Lenovo's [deployment catalog](https://download.lenovo.com/cdrt/td/catalogv2.xml) and per-type catalogs at `https://download.lenovo.com/catalog/<lowercase-type>_Win11.xml`. E485 uses `20ku_Win10.xml`. Package descriptors and payloads come from `https://download.lenovo.com/pccbbs/mobiles/`.

The verification chain is:

1. Fetch the model catalog over HTTPS and preserve its bytes, URL, and retrieval date.
2. Read each entry's `location` and `checksum`; verify the downloaded package XML descriptor's SHA-256 against that checksum.
3. Read `Files/Installer/File` in the verified descriptor. Its `Name`, `Size`, and `CRC` identify the installer; despite the field name `CRC`, the values used here are SHA-256 hashes.
4. Verify the installer hash before extraction. Extract it as data on Linux; do not run its Windows installer executable on the host.
5. Preserve the extracted package hierarchy and verify referenced CAT files. Test acceptance in Windows, which checks the actual signed driver packages.

This authenticates the retrieved bytes against Lenovo's HTTPS-published metadata. It is not an independent offline signature on the entire model catalog. Keep a frozen manifest for reproducing an old release; fresh catalog data may intentionally point to different bytes.

The selected source release dates span **2020-05-07 through 2026-09-14**. The retrieval date was 2026-09-18. An old release can still be the current OEM offering for an old device. Conversely, a newer individual package can supersede the version bundled in an older SCCM snapshot. Compare the live model catalogs, full deployment readmes, and supported hardware IDs. INF `DriverVer` dates do not substitute for the OEM release date: Intel chipset naming INFs may use deliberately historic dates.

| Record | Purpose |
| --- | --- |
| [driver-manifest.json](../research-drivers/driver-manifest.json) | All 171 sources, URLs and hashes, model provenance, and 876 INF paths/hashes/classes/versions |
| [source-checksums.sha256](../research-drivers/source-checksums.sha256) | Unique original installer names and verified SHA-256 values |
| [metadata/](../research-drivers/metadata/) | Frozen representative model catalogs, both T15g type catalogs, and package XML descriptors |
| [bootstrap-selected.json](../research-drivers/bootstrap-selected.json) | Final 169 separately selected installers; two E485 chipset components are added during staging |
| [bootstrap-excluded.json](../research-drivers/bootstrap-excluded.json) | Initial selection exclusions; read together with explicit script exclusions below |
| [t15g-all-descriptors.json](../research-drivers/t15g-all-descriptors.json), [t15g-selected.json](../research-drivers/t15g-selected.json), [t15g-excluded.json](../research-drivers/t15g-excluded.json) | Separate 36-descriptor T15g audit and selection |
| [hardware-ids.txt](../research-drivers/hardware-ids.txt) | Searchable tokens from INFs; model sections remain authoritative because tokens may also occur in comments or registry entries |
| [bootstrap-summary.json](../research-drivers/bootstrap-summary.json), [payload-validation.json](../research-drivers/payload-validation.json) | Counts, sizes, classes, CAT-reference checks, and path-collision checks |
| [latest-packs.json](../research-drivers/latest-packs.json), [t15g-sccm-catalog.json](../research-drivers/t15g-sccm-catalog.json) | Frozen deployment family/type/archive mappings |

## Selection lessons and exclusions

Category names are discovery hints, not a reliable allowlist. The first pass selected network, chipset, storage, input, and USB categories. A later unfiltered audit found these seven essential platform packages under **Software and Utilities**:

| Package ID | Function | Target group |
| --- | --- | --- |
| `r1jhe07w` | Intel HID event filter | L14/L15 Gen 2 Intel |
| `r1xhd03w` | Intel HID event filter | L14/L15 Gen 3 Intel |
| `nzbmt04w` | Intel platform monitoring | L14 Gen 5/6 Intel |
| `r3ehd02w` | Intel HID event filter | L14 Gen 7 Intel |
| `r2upp05w` | AMD PSP | L14 Gen 6 AMD 21S8/21S9 |
| `r2ipp03w` | AMD PSP | L14 Gen 5 AMD |
| `r2iai03w` | AMD I2C | L14 Gen 5 AMD |

T15g's TI USB-C power-delivery driver `n30tr02w` was under Display and Video Graphics. Its name and payload, rather than its category, established its relevance. Search all titles and inspect the INFs for I2C, GPIO, PSP, IOMMU, Serial IO, AHCI, RAID, RST, VMD, storage, Ethernet, and WLAN before declaring the selection complete.

The collection excludes BIOS/device-firmware updaters, WWAN/mobile-broadband, NPU, GPU, audio, camera, fingerprint, and optional application packages. Standalone smart-card/card-reader features were not a bootstrap requirement, although SDHost naming INFs can occur inside selected chipset packages. Selected packages retain their complete original contents, including supporting services or executables referenced by an INF; exclusion of an optional standalone application is not permission to strip arbitrary files out of a signed driver package.

The generic AMD S0i3 NetService network filter `r2ifc03w` was omitted as unnecessary for bootstrap connectivity. The old AMD power provisioning packages `r1kam04w` and `r1ypk01w` contain PPKG/EXE files and **zero INFs**, so they were not included in automatic INF staging. Their historical extraction results remain in `download-extraction-results.json`; zero INF is an explained exclusion here, not an unnoticed successful driver import.

Deduplicate identical installer payloads by filename plus SHA-256 while merging model/type provenance. The final collection keeps different OEM versions in separate directories. Do not deduplicate by package title, INF basename, apparent device name, or a single common hardware-ID token.

## Preserve the package layout and catalogs

Individual packages extract into `research-drivers/extracted/bootstrap/<package-id>/`, commonly below a literal `code$GetExtractPath$` directory. `stage_bootstrap.py` removes a single outer wrapper directory, retains everything beneath it, and writes `research-drivers/bootstrap-drivers/<package-id>/`. Release assembly copies that tree to the literal USB-root directory `$WinPEDriver$`.

E485's two chipset components come from `tp_e485_e585_w1064_202105.exe`, SHA-256 `f3d9b92f47e606bd20e4e4b8921da8e220095f7b4a85433ee6c46d7055f79777`. Their extraction paths are:

```text
research-drivers/extracted/E485/code$GetExtractPath$/Video/R0UA112W/AMDPSP/WT64A
research-drivers/extracted/E485/code$GetExtractPath$/Video/R0UA112W/SBDrv/SMBus/WT64A
```

They become `e485-amdpsp/` and `e485-smbus/`. Only these chipset subtrees were taken from the graphics bundle. E485's separate `r0uaw10w` Qualcomm and `r0urw12w` Realtek Wi-Fi packages address older or missing SCCM Wi-Fi content. Lenovo publishes this platform's drivers for Windows 10, and its original Ryzen CPUs are outside Microsoft's supported Windows 11 CPU list. Neither copying these drivers nor passing VM tests establishes official E485 support or physical compatibility.

Use [validate_payload.py](../research-drivers/validate_payload.py) to check both plain and decorated `CatalogFile` declarations. The frozen tree has 876 resolvable CAT references, zero empty CAT files, and no case-insensitive relative-path collisions. This is a structural check, not cryptographic signature verification. Preserve `SourceDisksFiles`, `CopyFiles`, architecture subfolders, coinstallers, extensions, and dependency payloads. A CAT file being present does not prove its covered files remain intact.

Different same-named files in distinct original directories are legitimate. Examples include ARM64 versus x64 power-service files, Intel ME `lib` versus `lib32`, and WinTab's root versus `ext` driver payload. Flattening these directories or deleting the apparently duplicate files can break the package. Firmware-class INFs are defensively removed by `stage_bootstrap.py`; none were present in this selected collection. If that exclusion ever becomes nonempty, review and exclude the source deliberately rather than treating silent INF removal as a complete firmware audit.

## Storage drivers and the limits of the VMD conclusion

The historical [all-descriptor-audit.json](../research-drivers/all-descriptor-audit.json) contains **403 descriptors from 15 representative L14/L15 Windows 11 family catalogs**. The phrase “all 403 ... E485/L14/L15” in the frozen research README overstates that specific audit's scope: `audit_storage.py` scans `*Win11.xml`, so E485's Windows 10 catalog was separate. T15g was added afterward through its separate 36-descriptor audit. Preserve the historical artifacts, but use this corrected scope when interpreting them.

For L14/L15 Gen 1 Intel, `r0zrs09w` contains `iaAHCIC.inf` and `iaStorAC.inf`, version **18.37.0.1002**. The audited Intel L14/L15 Gen 2–4 and L14 Gen 5–7 catalogs did not list a separate RST/VMD/`iaStorVD` package. The corresponding full SCCM readmes also lacked one. The saved L14 Gen 5 and Gen 6 WinPE readmes (`tp_mtl_pe11_202403.readme.txt` and `tp_arl_pe11_202504.readme.txt`) list Serial IO and Ethernet, without a separate RST/VMD storage package.

That evidence supports using inbox NVMe/AHCI drivers for those catalogued factory configurations. It does **not** prove that every BIOS setting, replacement controller, RAID arrangement, or future revision can boot without another driver. Do not generalize this inventory result into “all modern Intel machines do not need VMD.” A refresh must repeat the unfiltered audit and compare the actual controller IDs on any failing system.

T15g Gen 1 has a WM490 chipset, two NVMe slots, and RAID 0/1 capability. It explicitly requires preservation of its OEM storage option: `n2idg13w_p`, installer `n2idg13w.exe`, RST **17.11.0.1000**, including Optane-related components. Both its [package readme](https://download.lenovo.com/pccbbs/mobiles/n2idg13w.txt) and [full SCCM readme](https://download.lenovo.com/pccbbs/mobiles/tp_p15_mt20st-20su-p17_mt20sn-20sq-t15g_mt20ur-20us_w11_22_202310.txt) identify that package. Its INFs cover PCH/RST IDs including `PCI\VEN_8086&DEV_06D6&CC_0104`, `PCI\VEN_8086&DEV_06D7&CC_0104`, and `PCI\VEN_8086&DEV_282A&CC_0104`. No separate VMD package was listed for T15g Gen 1.

Some T15g RST 17.11 IDs overlap L14/L15 Gen 1 RST 18.37. Windows ranks matching packages across the entire offered collection, so the presence of the model-specific directory does not guarantee that its version wins. Both INF sets explicitly list the overlapping IDs, but physical storage binding was not tested. Keep each version intact and identifiable for troubleshooting. If Setup cannot see a disk, record its controller/BIOS mode and use **Load driver** with the appropriate OEM folder; do not change an existing installation's storage mode casually.

Microsoft documents [$WinPEDriver$ loading/injection limitations](https://learn.microsoft.com/en-us/troubleshoot/windows-client/setup-upgrade-and-drivers/limitations-dollar-sign-winpedriver-dollar-sign), including conflicts between versions already loaded in WinPE and those subsequently offered. Avoid injecting one storage-driver version into `boot.wim` while presenting another through `$WinPEDriver$`. The article contains older platform examples; installation testing on the actual release and target hardware is stronger evidence than assuming every historic behavior remains unchanged.

## Reproduce the frozen driver collection

Required tools are Python 3, `innoextract`, and GNU coreutils; `7z` was a fallback in the original downloader. Network access is needed only for missing installers. The recipes below operate in a new run directory and do not write a physical disk. Large package archives, extracted trees, and VM images are generated/cache artifacts and may be absent in a fresh checkout. In particular, the full E485 archive and disposable VM disks were removed after the original tests.

Create the isolated research directory and copy the frozen selection, results, and actual staging/check scripts:

```bash
set -euo pipefail
mkdir -p .runs
run_dir=$(mktemp -d "$PWD/.runs/driver-replay.XXXXXX")
mkdir -p "$run_dir/research-drivers"
cp research-drivers/stage_bootstrap.py \
   research-drivers/validate_payload.py \
   research-drivers/bootstrap-selected.json \
   research-drivers/download-extraction-results.json \
   research-drivers/driver-manifest.json \
   "$run_dir/research-drivers/"
```

If the existing extracted cache is intact, this is the shortest replay. The literal `code$GetExtractPath$` directory names are preserved by the copy:

```bash
set -euo pipefail
cp -a --reflink=auto research-drivers/extracted "$run_dir/research-drivers/"
python3 "$run_dir/research-drivers/stage_bootstrap.py"
python3 "$run_dir/research-drivers/validate_payload.py"
```

If only the finalized `bootstrap-drivers/` cache is available, it can instead be copied unchanged into a new release's `$WinPEDriver$` tree and checked against the frozen manifests. It is not an extracted-source cache for `stage_bootstrap.py`: that script still inspects the expected `extracted/` roots. Use the repository's assembly and source/staged hash-comparison instructions for that route.

If the extracted cache is missing, the following frozen-manifest recipe downloads missing installers, verifies every expected SHA-256, and uses the same `innoextract -s -d` command as the original workflow. Run it **instead of** the extracted-cache copy above, before running the two staging/check commands. It is a reconstruction recipe assembled from the original scripts, not a new generic Lenovo updater. It intentionally fails if a new extraction root already exists; use another run directory rather than mixing partial extractions.

```bash
set -euo pipefail
DRIVER_REPLAY_DIR="$run_dir/research-drivers" python3 - <<'PY'
from pathlib import Path
import hashlib, json, os, shutil, subprocess, urllib.request

out = Path(os.environ['DRIVER_REPLAY_DIR'])
manifest = json.loads((out / 'driver-manifest.json').read_text())
selected = json.loads((out / 'bootstrap-selected.json').read_text())
cache = Path('research-drivers/packages')
packages = out / 'packages'
packages.mkdir()

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

files = {}
for source in manifest['sources']:
    for f in source['files']:
        if f['name'] in files:
            assert files[f['name']]['sha256'].lower() == f['sha256'].lower()
        files[f['name']] = f
for name, f in files.items():
    dest = packages / name
    cached = cache / name
    if cached.exists() and digest(cached) == f['sha256'].lower():
        shutil.copyfile(cached, dest)
    else:
        partial = dest.with_suffix(dest.suffix + '.part')
        with urllib.request.urlopen(f['url'], timeout=120) as response, partial.open('wb') as stream:
            shutil.copyfileobj(response, stream)
        assert digest(partial) == f['sha256'].lower(), name
        partial.rename(dest)
    assert digest(dest) == f['sha256'].lower(), name

def extract(installer, destination):
    destination.mkdir(parents=True, exist_ok=False)
    with (destination / 'extraction.log').open('w') as log:
        subprocess.run(['innoextract', '-s', '-d', str(destination), str(installer)],
                       stdout=log, stderr=subprocess.STDOUT, check=True)

results = []
for source in selected:
    assert len(source['files']) == 1, source['id']
    dest = out / 'extracted' / 'bootstrap' / source['id']
    extract(packages / source['files'][0]['name'], dest)
    count = sum(p.suffix.lower() == '.inf' for p in dest.rglob('*') if p.is_file())
    assert count > 0, source['id']
    results.append([source['id'], count, 0])
extract(packages / 'tp_e485_e585_w1064_202105.exe', out / 'extracted' / 'E485')
# Fresh replay results cover the selected installers, not the historic excluded packages.
(out / 'download-extraction-results.json').write_text(json.dumps(results, indent=2))
PY
python3 "$run_dir/research-drivers/stage_bootstrap.py"
python3 "$run_dir/research-drivers/validate_payload.py"
```

The original frozen source-check file can also check an available installer cache directly:

```bash
set -euo pipefail
(cd research-drivers/packages && sha256sum -c ../source-checksums.sha256)
```

A missing cached installer causes that command to fail; retrieve it from the manifest rather than ignoring the failure. For the isolated replay, compare regenerated INF identities and byte/count totals against the frozen collection:

```bash
set -euo pipefail
DRIVER_REPLAY_DIR="$run_dir/research-drivers" python3 - <<'PY'
from pathlib import Path
import json, os
old = Path('research-drivers')
new = Path(os.environ['DRIVER_REPLAY_DIR'])
def infs(root):
    data = json.loads((root / 'driver-manifest.json').read_text())
    return {i['path']: i['sha256'] for i in data['infs']}
assert infs(old) == infs(new)
a = json.loads((old / 'bootstrap-summary.json').read_text())
b = json.loads((new / 'bootstrap-summary.json').read_text())
for field in ('packages', 'infs', 'bytes', 'classes', 'types'):
    assert a[field] == b[field], field
print('Frozen replay matches source INF hashes and expected collection totals.')
PY
```

This comparison does not replace release assembly's **all-file** SHA-256 comparison. The original release compared every one of the 5,166 source/staged files; see [final-driver-staging-validation.json](../verification/final-driver-staging-validation.json). CAT-reference validation alone cannot establish equality of all driver payload bytes.

## Refresh from Lenovo's current catalogs

Refreshing is a new release with new evidence. Do not replace the frozen 2026-09-18 metadata in place or retain its retrieval date on newly fetched data. Start a separate `.runs/<unique>/` directory. Revisit the target family/type list when extending coverage; the 49-type list only describes this release.

This read-only download recipe obtains a fresh catalog for **every currently covered type**, including E485 Win10 and both T15g types, then verifies every referenced descriptor without category filtering. It does not select or download the driver installers. It preserves both model and package provenance for the subsequent selection review.

```bash
set -euo pipefail
mkdir -p .runs
refresh_dir=$(mktemp -d "$PWD/.runs/driver-refresh.XXXXXX")
DRIVER_REFRESH_DIR="$refresh_dir" python3 - <<'PY'
from pathlib import Path
import datetime, hashlib, json, os, urllib.request, xml.etree.ElementTree as ET

out = Path(os.environ['DRIVER_REFRESH_DIR'])
metadata = out / 'metadata'
metadata.mkdir()
types = json.loads(Path('research-drivers/bootstrap-summary.json').read_text())['types']
base = 'https://download.lenovo.com/'
def fetch(url):
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()
(out / 'catalogv2.xml').write_bytes(fetch(base + 'cdrt/td/catalogv2.xml'))
entries = {}
for machine_type in types:
    name = machine_type.lower() + ('_Win10.xml' if machine_type == '20KU' else '_Win11.xml')
    url = base + 'catalog/' + name
    data = fetch(url)
    (metadata / name).write_bytes(data)
    for item in ET.fromstring(data):
        location = item.findtext('location')
        checksum = item.findtext('checksum').lower()
        if location in entries:
            assert entries[location]['metadata_sha256'] == checksum, location
        entry = entries.setdefault(location, {'metadata_url': location,
            'metadata_sha256': checksum, 'types': [], 'catalogs': [], 'categories': []})
        entry['types'].append(machine_type)
        entry['catalogs'].append(url)
        entry['categories'].append(item.findtext('category'))
for url, entry in entries.items():
    data = fetch(url)
    assert hashlib.sha256(data).hexdigest() == entry['metadata_sha256'], url
    path = metadata / url.rsplit('/', 1)[-1]
    assert not path.exists() or path.read_bytes() == data, path
    path.write_bytes(data)
    xml = ET.fromstring(data)
    entry.update(id=xml.get('id'), title=xml.findtext('Title/Desc'),
                 version=xml.get('version'), date=xml.findtext('ReleaseDate'))
    entry['files'] = [{'name': f.findtext('Name'), 'sha256': f.findtext('CRC'),
        'size': int(f.findtext('Size')), 'url': url.rsplit('/', 1)[0] + '/' + f.findtext('Name')}
        for f in xml.findall('Files/Installer/File')]
(out / 'all-current-descriptors.json').write_text(json.dumps({
    'retrieved_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'types': types, 'descriptors': list(entries.values())}, indent=2))
print('Fetched', len(types), 'model catalogs and', len(entries), 'verified descriptors.')
PY
```

If Lenovo changes a catalog during the download and two references disagree about a descriptor's hash, stop and retrieve a consistent new snapshot. Do not weaken the hash check. Read all descriptor titles and the latest full SCCM/WinPE readmes, review network alternatives and boot/platform categories, then create the new selection. Preserve exact-byte deduplication and provenance. Changes to package IDs, installer formats, E485 component paths, or the model map require adapting the historical helpers rather than assuming the old constants remain valid.

### What the retained research scripts actually do

These commands are useful in a disposable copy with their stated inputs. They are not a complete one-command refresh pipeline:

| Command | Inputs and limits |
| --- | --- |
| `python3 research-drivers/collect_metadata.py` | Reads `latest-packs.json`, chooses the **first type** of each deployment family, excludes L14P, and reuses already-existing metadata. Filters categories before fetching descriptors. It misses the seven platform additions and does not independently refresh all 49 types. Writes `bootstrap-candidates.json`. |
| `python3 research-drivers/audit_storage.py > research-drivers/storage-audit.log` | Scans every saved `*Win11.xml`, verifies/fetches all referenced descriptors regardless of category, and writes `all-descriptor-audit.json`. Excludes Win10 by its glob. Rerunning now includes T15g catalogs and changes the historic 403 count; it is an audit of the files present, not a fixed-count test. |
| `python3 research-drivers/download_bootstrap.py` | Filters `bootstrap-candidates.json`, overwrites selection/exclusion/result JSON, deduplicates original payloads, downloads and verifies them, then extracts with `innoextract` and a `7z` fallback. It is **not** a final-manifest replay command and would discard later manual additions from the selection. |
| `python3 research-drivers/add_essential_platform.py` | Reads the complete descriptor audit, `metadata/`, and `latest-packs.json`; downloads and merges **seven hardcoded IDs**. Useful for this snapshot, not for discovering their future replacements. |
| `python3 research-drivers/add_t15g.py` | Reads the separately prepared `t15g-all-descriptors.json` and selects **15 hardcoded IDs**; three matched existing payloads, so it added 12 directories. Merges types/provenance by exact filename/hash. It does not fetch the T15g catalogs itself; repeated runs can append duplicate provenance entries. |
| `python3 research-drivers/stage_bootstrap.py` | Requires selected extracted roots plus the exact E485 component paths. Regenerates manifests, coverage, hashes, and summary. It skips copying destinations that already exist and does **not** remove stale package directories; use an empty output tree for a changed selection. Its recorded retrieval date is hardcoded to 2026-09-18 and must be revised for a new release. |
| `python3 research-drivers/validate_payload.py` | Checks the current output tree's CAT references, empty CATs, and case-insensitive paths. Reports differing basenames retained in distinct OEM directories. Does not verify Windows trust/signatures or infer physical compatibility. |

The initial global-catalog/family-map construction, the T15g descriptor JSON construction, some readme retrieval/conversion, final selection adjustments, and initial VM input-image creation were one-off orchestration. Their evidence is retained, but there is no claim that executing the seven scripts in sequence reconstructs every decision. Use the frozen replay above for byte reproduction, or repeat the full selection review for a refresh. Resolve download/extraction errors explicitly before staging; an extraction process exiting successfully with no INF is not enough.

## Windows acceptance tests and interpretation

The original offline Home installation tested **159 packages / 786 INF paths** before T15g was added. Those paths represent **415 distinct INF SHA-256 values**. The installed Windows image had **416 third-party entries**: 415 Lenovo entries whose per-class totals matched those distinct INFs, plus Microsoft's `prnms009.inf` printer entry. The local `MediaTest` account reached the desktop without a network adapter, and `Confirm-SecureBootUEFI` returned `True`. See [baseline driver-store comparison](../verification/local/driver-store-comparison.json) and [local test notes](../verification/local/test-notes.md).

The later T15g test booted that installed system directly, with no installer image or network attached. It supplied **12 added source packages / 90 INF files** on a separate read-only FAT virtual removable disk and exported logs to another writable FAT disk. An elevated command added packages to the store without requesting device installation:

```powershell
pnputil.exe /add-driver D:\Drivers\*.inf /subdirs
```

`D:` is an example input-drive letter, not a fixed assumption. Microsoft's [PnPUtil syntax](https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/pnputil-command-syntax) distinguishes adding packages from the optional `/install` action. The test did not use `/install`, `/reboot`, or a force action. Its purpose was signature/payload acceptance without installing nonmatching drivers on the virtual devices.

PnPUtil reported **90 total, 90 added, exit code 0**. Fifty INF hashes were already present in the baseline. Forty distinct entries were added, producing **456 total third-party entries**. The new class counts matched the 40 distinct new source INF hashes:

| Class | New entries |
| --- | ---: |
| System | 20 |
| SoftwareComponent | 8 |
| Extension | 3 |
| Net | 3 |
| HIDClass | 2 |
| HDC | 1 |
| SCSIAdapter | 1 |
| Ports | 1 |
| SDHost | 1 |

Do not derive this count by counting every success message in the output. The two Thunderbolt host INFs each import three dependent packages; later passes over those dependent INFs report them as already present. There are 90 input blocks but 96 individual success messages. The authoritative comparison uses input INF hashes, the PnPUtil summary, and before/after store inventories.

The [T15g validation directory](../verification/t15g-windows-validation/) preserves `validation-summary.json`, `expected-results.json`, the exact `Validate.ps1`, exported before/after inventories, PnPUtil output, setup API logs, and [the final screenshot](../verification/t15g-windows-validation/15-validation-result.png). Secure Boot remained enabled and the VM shut down normally. This is evidence that Windows accepts the signed packages and their payloads. It does not test the T15g's physical storage mode, Wi-Fi/Ethernet function, graphics, suspend/resume, or which overlapping driver version wins on real hardware.

### Repeat the T15g acceptance test

Recreate the disposable baseline VM using the main test instructions first. Its `system.qcow2`, matching `vars.fd`, and vTPM state must belong to the same test installation. The disk images were deliberately removed after testing, so the saved launcher alone is not a runnable VM backup. A VM that has already imported the T15g drivers will correctly add zero new distinct entries on another run; restore/rebuild the baseline if you want to repeat the historical 416-to-456 comparison.

The saved [start-vm.sh](../verification/t15g-windows-validation/start-vm.sh) expects these paths under a run root:

```text
verification/local/system.qcow2
verification/local/vars.fd
verification/local/tpm/tpm2-00.permall
verification/t15g-windows-validation/input.img
verification/t15g-windows-validation/output.img
```

It boots the installed OS directly, uses `OVMF_CODE_4M.ms.fd` and the existing Secure Boot variables, attaches the input read-only, and omits network devices. It has no physical-device input. It still modifies the disposable system disk, NVRAM, and TPM state; do not share those between concurrently running VMs.

After setting `run_dir` to the isolated test run that contains the reconstructed baseline, create fresh removable inputs as follows. This requires `dosfstools` (`mkfs.vfat`) and `mtools` (`mmd`, `mcopy`) in addition to Python. The command refuses to overwrite existing test images.

```bash
set -euo pipefail
mkdir -p "$run_dir/verification/t15g-windows-validation"
cp verification/t15g-windows-validation/Validate.ps1 \
   verification/t15g-windows-validation/Run.cmd \
   verification/t15g-windows-validation/start-vm.sh \
   "$run_dir/verification/t15g-windows-validation/"
DRIVER_TEST_RUN="$run_dir" python3 - <<'PY'
from pathlib import Path
import json, os, shutil, subprocess

run = Path(os.environ['DRIVER_TEST_RUN'])
v = run / 'verification/t15g-windows-validation'
source = run / 'research-drivers/bootstrap-drivers'
if not source.is_dir():
    source = Path('research-drivers/bootstrap-drivers')
manifest = json.loads(Path('verification/t15g-windows-validation/input-manifest.json').read_text())
ids = manifest['packages']
assert len(ids) == 12
mkfs = shutil.which('mkfs.vfat') or '/usr/sbin/mkfs.vfat'
for name, size, label, fat in [('input.img', 1024**3, 'T15GINPUT', '32'),
                             ('output.img', 128 * 1024**2, 'T15GLOGS', '16')]:
    path = v / name
    with path.open('xb') as stream:
        stream.truncate(size)
    subprocess.run([mkfs, '-F', fat, '-n', label, str(path)], check=True)
subprocess.run(['mmd', '-i', str(v / 'input.img'), '::Drivers'], check=True)
for package in ids:
    assert (source / package).is_dir(), package
    subprocess.run(['mcopy', '-i', str(v / 'input.img'), '-s',
                    str(source / package), '::Drivers/'], check=True)
for name in ('Validate.ps1', 'Run.cmd'):
    subprocess.run(['mcopy', '-i', str(v / 'input.img'), str(v / name), '::/'], check=True)
PY
bash "$run_dir/verification/t15g-windows-validation/start-vm.sh"
```

The launcher needs host access to KVM and permission to create its local monitor/TPM sockets. It may require the environment's normal elevated execution mechanism. Do not resolve permission errors by attaching host disks or disabling Secure Boot. Use the existing [qmp.py](../scripts/qmp.py) to inspect the VM:

```bash
set -euo pipefail
python3 scripts/qmp.py "$run_dir/verification/t15g-windows-validation/qmp.sock" \
  screenshot "$run_dir/verification/t15g-windows-validation/desktop.png"
```

On the Windows desktop, **Win+X, A** opened the administrative Terminal reliably during the recorded test. Run-dialog attempts to launch `cmd` stalled, and typing immediately after opening a dialog lost the first character once. Allow UI transitions to complete and inspect the screen before sending the next input. Approve elevation within the disposable test VM, then run:

```powershell
$v = Get-Volume -FileSystemLabel T15GINPUT
powershell -NoProfile -ExecutionPolicy Bypass -File ($v.DriveLetter + ':\Validate.ps1')
```

The saved script locates output by the `T15GLOGS` label, records Secure Boot and the test account, captures `Get-WindowsDriver -Online` before/after inventories, logs PnPUtil, and copies setup API logs. Its account name is fixed to `MediaTest`; adapt it for a differently named test account. `NetworkAdapterPresent = false` in its JSON is a declared test configuration, not automatic device discovery; confirm the launcher's `-nic none` when relying on it. The frozen expected counts only apply to this exact baseline and driver delta.

Wait for `T15G VALIDATION COMPLETE` and inspect the result before shutting Windows down with `shutdown /s /t 0`. Confirm QEMU has exited, then stop only that test's owned vTPM process after verifying its PID/command line. Export the log image only after the guest has stopped writing it:

```bash
set -euo pipefail
mkdir -p "$run_dir/verification/t15g-windows-validation/exported"
mcopy -s -i "$run_dir/verification/t15g-windows-validation/output.img" \
  '::*' "$run_dir/verification/t15g-windows-validation/exported/"
```

Check exit status, failed input blocks, distinct added entries, per-class differences, and storage/network package identities. Preserve the logs and a final screenshot. Only then assemble or freeze a release and perform the independent source/staged all-file comparison. A future physical smoke test should explicitly check installation-disk visibility, desktop boot, each available Wi-Fi/Ethernet adapter, and device errors on representative machines from each covered platform group.
