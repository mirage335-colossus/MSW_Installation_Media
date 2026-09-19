#!/usr/bin/env python3
"""Bind the completed account tests to a fully hashed USB payload."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

base = Path(__file__).resolve().parent.parent
stage = base / 'staging'
verification = base / 'verification'
tested = json.loads((verification / 'account-tested-file-sha256.json').read_text())
for name, expected in tested.items():
    with (stage / name).open('rb') as f:
        assert hashlib.file_digest(f, 'sha256').hexdigest() == expected, name
for name in ('local-home-desktop.png', 'local-account-secureboot.png',
             'cloud-microsoft-signin.png', 'cloud-test-notes.md'):
    assert (stage / 'Documentation/Validation' / name).is_file(), name
drivers = json.loads((verification / 'final-driver-staging-validation.json').read_text())
assert drivers['all_file_sha256_equal'] and drivers['files_compared'] == 5166

lines = []
total = 0
for p in sorted(stage.rglob('*')):
    if not p.is_file() or p == stage / 'SHA256SUMS.txt':
        continue
    assert not p.is_symlink(), p
    assert p.stat().st_size < 2**32, p
    name = p.relative_to(stage).as_posix()
    with p.open('rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest()
    prefix = '\\' if '\\' in name or '\n' in name else ''
    escaped = name.replace('\\', '\\\\').replace('\n', '\\n')
    lines.append(f'{prefix}{digest}  {escaped}\n')
    total += p.stat().st_size
(stage / 'SHA256SUMS.txt').write_text(''.join(lines))
report = {
    'prepared_at_utc': datetime.now(timezone.utc).isoformat(),
    'account_validation': 'passed',
    'account_validation_scope': 'Offline Home local-account desktop and online Pro Microsoft sign-in form; no cloud credentials supplied.',
    'tested_file_sha256': tested,
    'final_driver_validation': 'final-driver-staging-validation.json',
    'final_driver_manifest_sha256': hashlib.sha256((stage / 'Documentation/driver-manifest.json').read_bytes()).hexdigest(),
    'sha256_manifest_sha256': hashlib.sha256((stage / 'SHA256SUMS.txt').read_bytes()).hexdigest(),
    'payload_files': len(lines),
    'payload_bytes': total,
    'physical_device_functionality_tested': False,
}
(verification / 'validation-ready.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
