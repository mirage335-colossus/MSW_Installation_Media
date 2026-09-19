from pathlib import Path
import collections
import hashlib
import json
import re

root = Path(__file__).resolve().parent
payload = root / 'bootstrap-drivers'
references = []
missing = []
collisions = []
different = []
zero = []

for package in sorted(payload.iterdir()):
    if not package.is_dir():
        continue
    paths = collections.defaultdict(list)
    basenames = collections.defaultdict(list)
    for path in package.rglob('*'):
        if not path.is_file():
            continue
        relative = str(path.relative_to(package))
        paths[relative.casefold()].append(relative)
        basenames[path.name.casefold()].append(path)
        if path.suffix.lower() == '.cat' and path.stat().st_size == 0:
            zero.append(str(path.relative_to(payload)))
        if path.suffix.lower() != '.inf':
            continue
        data = path.read_bytes()
        text = data.decode('utf-16', errors='replace') if data.startswith((b'\xff\xfe', b'\xfe\xff')) else data.decode('cp1252', errors='replace')
        siblings = {p.name.casefold(): p for p in path.parent.iterdir() if p.is_file()}
        for name in re.findall(r'^\s*CatalogFile(?:\.[^=\s]+)?\s*=\s*([^;\r\n]+)', text, re.I | re.M):
            name = name.strip().strip('"')
            reference = [str(path.relative_to(payload)), name]
            references.append(reference)
            if name.casefold() not in siblings:
                missing.append(reference)
    collisions.extend([package.name, entries] for entries in paths.values() if len(entries) > 1)
    for name, entries in basenames.items():
        if len(entries) > 1 and len({hashlib.sha256(p.read_bytes()).digest() for p in entries}) > 1:
            different.append([package.name, name, sorted(str(p.relative_to(package)) for p in entries)])

report = {
    'catalog_references': len(references),
    'catalog_files_present': len(references) - len(missing),
    'missing_catalogs': missing,
    'zero_length_catalogs': len(zero),
    'case_insensitive_relative_path_collisions': len(collisions),
    'same_basename_different_relative_directories': different,
}
(root / 'payload-validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
assert not missing and not zero and not collisions
