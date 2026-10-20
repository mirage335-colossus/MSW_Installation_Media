#!/usr/bin/env python3
"""Read-only checks for the frozen rebuild's tracked inputs and optional host/cache."""
import argparse
import collections
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import sys
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True

REQUIRED = (
    "README.md .gitignore docs/README.md docs/from-git-clone.md docs/runbook.md "
    "docs/ready-to-flash-image.md docs/testing-and-acceptance.md "
    "docs/account-choice-and-testing.md docs/driver-maintenance.md "
    "docs/source-media-and-secure-boot.md docs/lessons-learned.md "
    "docs/templates/test-report.md "
    "scripts/check-clone-inputs.py tests/test_clone_inputs.py scripts/prepare-media.py scripts/Install-Drivers.cmd "
    "scripts/build-test-media.sh scripts/start-test-vm.sh scripts/qmp.py "
    "scripts/finalize-media.py scripts/build-release-image.sh scripts/verify-release-payload.py "
    "scripts/write-verified-usb.sh scripts/start-physical-usb-test.sh "
    "research-accounts/README.md research-accounts/ACCOUNT-CHOICES.txt "
    "research-accounts/MediaSetup.cmd research-accounts/winpeshl.ini "
    "research-accounts/MSW11-MEDIA.ID research-accounts/Enable-E485-Compatibility.cmd "
    "research-accounts/profiles/local.xml research-accounts/profiles/microsoft.xml "
    "research-drivers/README.md research-drivers/stage_bootstrap.py "
    "research-drivers/validate_payload.py research-drivers/bootstrap-selected.json "
    "research-drivers/download-extraction-results.json research-drivers/driver-manifest.json "
    "research-drivers/bootstrap-summary.json research-drivers/source-checksums.sha256 "
    "research-drivers/model-coverage.tsv downloads/windows11-iso-provenance.json "
    "research/iso-acquisition/README.md staging/README.txt staging/SHA256SUMS.txt "
    "verification/validation-ready.json verification/secureboot/README.md"
).split()
SHA256 = re.compile(r"[0-9a-fA-F]{64}")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def check_sources(root):
    tracked = set(subprocess.check_output(
        ["git", "-C", str(root), "ls-files", "-z"], text=True).split("\0"))
    checked = set()

    def source(name):
        require(name in tracked, "Required file is not tracked: " + name)
        path = root / name
        require(stat.S_ISREG(path.lstat().st_mode), "Not a regular source file: " + name)
        checked.add(name)
        return path

    for name in REQUIRED:
        source(name)
    iso = json.loads(source("downloads/windows11-iso-provenance.json").read_text())
    filename, sha = iso["filename"], iso["official_sha256"].lower()
    require(Path(filename).name == filename and SHA256.fullmatch(sha), "Invalid ISO identity")
    require(iso["verified_sha256"].lower() == sha, "ISO provenance hashes disagree")
    checksum = source("downloads/" + filename + ".sha256").read_text().split()
    require(checksum == [sha, filename], "ISO checksum companion disagrees")
    prepare = source("scripts/prepare-media.py").read_text()
    require(f"expected = '{sha}'" in prepare and f"downloads/{filename}" in prepare,
            "Preparation script does not pin this ISO")

    selected = json.loads(source("research-drivers/bootstrap-selected.json").read_text())
    manifest = json.loads(source("research-drivers/driver-manifest.json").read_text())
    summary = json.loads(source("research-drivers/bootstrap-summary.json").read_text())
    sources = {item["id"]: item for item in manifest["sources"]}
    require(len(sources) == len(manifest["sources"]) == summary["packages"], "Duplicate/count error in sources")
    require(len({s["id"] for s in selected}) == len(selected), "Duplicate selected package")
    require(set(sources) == {s["id"] for s in selected} | {"e485-amdpsp", "e485-smbus"},
            "Final driver sources differ from selection plus E485 components")
    downloads = {}
    for entry in manifest["sources"]:
        for item in entry["files"]:
            name, expected = item["name"], item["sha256"].lower()
            url = urlsplit(item["url"])
            require(Path(name).name == name and SHA256.fullmatch(expected), "Invalid driver file identity")
            require(url.scheme == "https" and url.hostname == "download.lenovo.com",
                    "Driver source is not Lenovo HTTPS: " + name)
            if name in downloads:
                require(downloads[name]["sha256"].lower() == expected, "Conflicting driver hash: " + name)
            downloads[name] = item
    for entry in selected:
        require(entry["files"] == sources[entry["id"]]["files"], "Selected download differs: " + entry["id"])
        url = urlsplit(entry["metadata_url"])
        descriptor = source("research-drivers/metadata/" + Path(url.path).name)
        require(digest(descriptor) == entry["metadata_sha256"].lower(), "Descriptor hash mismatch: " + entry["id"])
        xml = ET.parse(descriptor)
        installer = xml.findall("./Files/Installer/File")
        actual = {(f.findtext("Name"), f.findtext("CRC").lower()) for f in installer}
        expected = {(f["name"], f["sha256"].lower()) for f in entry["files"]}
        require(actual == expected, "Descriptor installer identity differs: " + entry["id"])
        for catalog in entry.get("catalogs", []):
            source("research-drivers/metadata/" + Path(urlsplit(catalog).path).name)
    expected_lines = {f["sha256"].lower() + "  " + n for n, f in downloads.items()}
    require(set(source("research-drivers/source-checksums.sha256").read_text().splitlines()) == expected_lines,
            "Driver checksum list differs from manifest")
    infs = manifest["infs"]
    require(len(infs) == len({i["path"] for i in infs}) == summary["infs"], "INF count/path mismatch")
    require(dict(collections.Counter(i["class"] or "unknown" for i in infs)) == summary["classes"],
            "Driver class totals disagree")
    require(sorted({t for entry in sources.values() for t in entry["types"]}) == summary["types"],
            "Machine-type coverage disagrees")
    for profile in ("local", "microsoft"):
        xml = ET.parse(source(f"research-accounts/profiles/{profile}.xml"))
        forbidden = {"DiskConfiguration", "ImageInstall", "UserAccounts", "AutoLogon",
                     "SkipMachineOOBE", "SkipUserOOBE"}
        require(not any(n.tag.split("}")[-1] in forbidden for n in xml.iter()),
                "Unexpected unattended action in " + profile)
    return iso, downloads, {
        "required_tracked_files_checked": len(checked),
        "driver_sources": len(sources), "unique_driver_installers": len(downloads),
        "inf_paths": len(infs), "machine_types": len(summary["types"]),
        "iso_filename": filename, "iso_sha256": sha,
    }


def check_downloads(root, iso, drivers):
    inputs = [(root / "downloads" / iso["filename"], iso["official_sha256"], iso["size_bytes"])]
    inputs += [(root / "research-drivers/packages" / name, item["sha256"], item.get("size"))
               for name, item in sorted(drivers.items())]
    errors = []
    for path, expected, size in inputs:
        if not path.is_file() or path.is_symlink():
            errors.append("Missing regular download: " + str(path.relative_to(root)))
        elif size is not None and path.stat().st_size != size:
            errors.append("Wrong download size: " + str(path.relative_to(root)))
        elif digest(path) != expected.lower():
            errors.append("Download SHA-256 mismatch: " + str(path.relative_to(root)))
    return errors


def check_preserved(root, cache, iso):
    """Verify the existing ISO and final driver files; original EXEs are optional."""
    errors = check_downloads(cache, iso, {})
    spec = importlib.util.spec_from_file_location("payload_verifier", root / "scripts/verify-release-payload.py")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    try:
        ready = helper.read_json(root / "verification/validation-ready.json")
        manifest = root / "staging/SHA256SUMS.txt"
        helper.require(helper.digest(manifest) == ready["sha256_manifest_sha256"],
                       "Frozen payload checksum manifest differs from the recorded build")
        helper.require(helper.digest(root / "research-drivers/driver-manifest.json") ==
                       ready["final_driver_manifest_sha256"], "Frozen driver manifest differs")
        prefix = "$WinPEDriver$/"
        expected = {name[len(prefix):]: sha for name, sha in helper.parse_manifest(manifest).items()
                    if name.startswith(prefix)}
        payload = cache / "research-drivers/bootstrap-drivers"
        files, _, _ = helper.scan_tree(payload)
        helper.require(bool(expected) and set(files) == set(expected), "Preserved driver file inventory differs")
        for name, sha in expected.items():
            helper.require(helper.digest(payload / name) == sha, "Preserved driver hash mismatch: " + name)
    except (helper.VerificationError, OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(str(exc))
    return errors


def check_host(root):
    errors = []
    commands = ("git bash 7z wimlib-imagex innoextract rsync mtype qemu-system-x86_64 "
                "qemu-img swtpm sudo mount umount mountpoint truncate sync "
                "sha256sum cmp timeout").split()
    # Privileged scripts use sudo's PATH or the builder's explicit system PATH.
    for name in commands:
        if not shutil.which(name):
            errors.append("Missing executable in PATH: " + name)
    for name in ("sfdisk", "losetup", "mkfs.vfat", "fsck.vfat"):
        if not any(os.access(Path(p) / name, os.X_OK) for p in ("/usr/sbin", "/sbin")):
            errors.append("Missing system executable: " + name)
    if importlib.util.find_spec("PIL") is None:
        errors.append("Python Pillow is required by the QMP screenshot helper")
    if platform.system() != "Linux" or platform.machine().lower() not in ("x86_64", "amd64"):
        errors.append("Recorded build/VM workflow requires x86-64 Linux")
    for name in ("OVMF_CODE_4M.ms.fd", "OVMF_VARS_4M.ms.fd"):
        if not os.access(Path("/usr/share/OVMF") / name, os.R_OK):
            errors.append("Missing readable Microsoft-enrolled firmware: " + name)
    if not os.access("/dev/kvm", os.R_OK | os.W_OK):
        errors.append("No current-user read/write access to /dev/kvm; VM tests unavailable in this environment")
    if not Path("/dev/loop-control").exists():
        errors.append("No /dev/loop-control visible; image loop operations unavailable in this environment")
    suffix = ".runs/a/verification/t15g-windows-validation/tpm.sock"
    if len(os.fsencode(root / suffix)) > 107:
        errors.append("Default run root is too long for Unix sockets; choose a shorter actual checkout/run path")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--downloads", action="store_true", help="Require and hash the ISO and all 170 frozen installers")
    parser.add_argument("--preserved", action="store_true", help="Require and hash the ISO and exact preserved driver payload")
    parser.add_argument("--cache-root", type=Path, help="Read binary inputs from this directory instead of the checkout")
    parser.add_argument("--host", action="store_true", help="Also inspect commands, firmware and visible VM/loop prerequisites")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable report to stdout")
    args = parser.parse_args()
    root = args.root.resolve()
    report = {"scope": "Frozen rebuild inputs only; not a build, boot or account test",
              "source_inputs": "not_checked", "downloads": "not_checked",
              "preserved_inputs": "not_checked", "host": "not_checked", "errors": []}
    try:
        require(sys.version_info >= (3, 11), "Python 3.11+ required")
        require(not sys.flags.optimize and not os.environ.get("PYTHONOPTIMIZE"),
                "Unset PYTHONOPTIMIZE and do not use python -O; existing build guards use assertions")
        iso, drivers, details = check_sources(root)
        report.update(details)
        report["source_inputs"] = "passed"
        cache = args.cache_root.resolve() if args.cache_root else root
        if args.downloads:
            errors = check_downloads(cache, iso, drivers)
            report["downloads"] = "failed" if errors else "passed"
            report["errors"].extend(errors)
        if args.preserved:
            errors = check_preserved(root, cache, iso)
            report["preserved_inputs"] = "failed" if errors else "passed"
            report["errors"].extend(errors)
        if args.host:
            errors = check_host(root)
            report["host"] = "failed" if errors else "passed"
            report["errors"].extend(errors)
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError, subprocess.CalledProcessError) as exc:
        report["errors"].append(str(exc))
    report["status"] = "failed" if report["errors"] else "passed"
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Source inputs: {report['source_inputs']}; downloads: {report['downloads']}; "
              f"preserved inputs: {report['preserved_inputs']}; host: {report['host']}")
        for error in report["errors"]:
            print("FAIL: " + error)
        if report["source_inputs"] == "passed":
            print(f"{report['driver_sources']} driver sources, {report['unique_driver_installers']} installers, "
                  f"{report['inf_paths']} INF paths, {report['machine_types']} machine types.")
        print(report["scope"])
    return 1 if report["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
