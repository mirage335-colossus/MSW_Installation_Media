"""Small failure-path tests; no network, disk devices, vendor binaries or sudo."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("clone_inputs", ROOT / "scripts/check-clone-inputs.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class SourceChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        names = set(checker.REQUIRED)
        names.update(p.relative_to(ROOT).as_posix() for p in (ROOT / "research-drivers/metadata").iterdir() if p.is_file())
        names.update(p.relative_to(ROOT).as_posix() for p in (ROOT / "downloads").glob("*.sha256"))
        for name in names:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        self.git("init", "-q")
        self.git("add", ".")

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)

    def test_tracked_snapshot_without_binary_downloads(self):
        iso, drivers, result = checker.check_sources(self.root)
        self.assertEqual((result["driver_sources"], result["unique_driver_installers"],
                          result["inf_paths"], result["machine_types"]), (171, 170, 876, 49))
        self.assertEqual(len(checker.check_downloads(self.root, iso, drivers)), 171)

    def test_existing_but_untracked_profile_is_rejected(self):
        name = "research-accounts/profiles/local.xml"
        self.git("rm", "--cached", name)
        self.assertTrue((self.root / name).is_file())
        with self.assertRaisesRegex(ValueError, "not tracked"):
            checker.check_sources(self.root)

    def test_missing_required_source_is_rejected(self):
        (self.root / "scripts/prepare-media.py").unlink()
        with self.assertRaises(FileNotFoundError):
            checker.check_sources(self.root)

    def test_modified_driver_descriptor_is_rejected(self):
        entry = json.loads((self.root / "research-drivers/bootstrap-selected.json").read_text())[0]
        name = entry["metadata_url"].rsplit("/", 1)[1]
        path = self.root / "research-drivers/metadata" / name
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "Descriptor hash mismatch"):
            checker.check_sources(self.root)

    def test_incomplete_driver_checksum_inventory_is_rejected(self):
        path = self.root / "research-drivers/source-checksums.sha256"
        path.write_text("\n".join(path.read_text().splitlines()[1:]) + "\n")
        with self.assertRaisesRegex(ValueError, "checksum list differs"):
            checker.check_sources(self.root)


class PreservedCacheChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ("scripts", "downloads", "staging", "verification",
                          "research-drivers/bootstrap-drivers/package"):
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "scripts/verify-release-payload.py",
                        self.root / "scripts/verify-release-payload.py")
        (self.root / "downloads/test.iso").write_bytes(b"test ISO fixture")
        self.driver = self.root / "research-drivers/bootstrap-drivers/package/network.inf"
        self.driver.write_bytes(b"test driver fixture")
        (self.root / "research-drivers/driver-manifest.json").write_text("{}\n")
        (self.root / "staging/SHA256SUMS.txt").write_text(
            checker.digest(self.driver) + "  $WinPEDriver$/package/network.inf\n")
        ready = {
            "sha256_manifest_sha256": checker.digest(self.root / "staging/SHA256SUMS.txt"),
            "final_driver_manifest_sha256": checker.digest(self.root / "research-drivers/driver-manifest.json"),
        }
        (self.root / "verification/validation-ready.json").write_text(json.dumps(ready))
        self.iso = {"filename": "test.iso", "official_sha256": checker.digest(self.root / "downloads/test.iso"),
                    "size_bytes": (self.root / "downloads/test.iso").stat().st_size}

    def check(self):
        return checker.check_preserved(self.root, self.root, self.iso)

    def test_exact_cache_passes_without_original_installers(self):
        self.assertEqual(self.check(), [])

    def test_changed_driver_fails(self):
        self.driver.write_bytes(b"changed")
        self.assertIn("hash mismatch", " ".join(self.check()))

    def test_extra_driver_file_fails(self):
        self.driver.with_name("extra.sys").write_bytes(b"extra")
        self.assertIn("inventory differs", " ".join(self.check()))

    def test_missing_driver_file_fails(self):
        self.driver.unlink()
        self.assertIn("inventory differs", " ".join(self.check()))

    def test_symlink_fails(self):
        content = self.root / "other"
        self.driver.rename(content)
        self.driver.symlink_to(content)
        self.assertIn("Symlink", " ".join(self.check()))

    def test_wrong_iso_fails(self):
        path = self.root / "downloads/test.iso"
        path.write_bytes(b"x" * self.iso["size_bytes"])
        self.assertIn("SHA-256 mismatch", " ".join(self.check()))


if __name__ == "__main__":
    unittest.main()
