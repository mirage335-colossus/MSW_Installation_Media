#!/usr/bin/env python3
"""Verify frozen installer payloads and regular-file release images; never write a device."""

import argparse
import collections
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import struct
import sys
import unicodedata
from datetime import datetime, timezone

IMAGE_BYTES = 61_991_813_120
SECTOR_BYTES = 512
PARTITION_START = 2048
PARTITION_SECTORS = IMAGE_BYTES // SECTOR_BYTES - PARTITION_START
CLUSTER_BYTES = 32768
FAT_HEADS = 255
FAT_SECTORS_PER_TRACK = 63
MANIFEST = 'SHA256SUMS.txt'
PUBLIC_IMAGE = 'MSW11-Lenovo-x64.img'


class VerificationError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def regular(path):
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode), f'Not a regular, nonsymlink file: {path}')
    return info


def digest(path):
    regular(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode), f'Not a regular file: {path}')
        value = hashlib.file_digest(stream, 'sha256').hexdigest()
        after = os.fstat(stream.fileno())
    require((before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
            (after.st_size, after.st_mtime_ns, after.st_ctime_ns), f'File changed while hashing: {path}')
    return value


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'Duplicate JSON key: {key}')
        result[key] = value
    return result


def read_json(path):
    regular(path)
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique_object)


def write_json(path, data):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(data, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def sha_value(value, label):
    require(isinstance(value, str) and re.fullmatch(r'[0-9a-fA-F]{64}', value), f'Invalid SHA-256: {label}')
    return value.lower()


def integer(value, label):
    require(type(value) is int and value >= 0, f'Invalid nonnegative integer: {label}')
    return value


def safe_name(name):
    require(isinstance(name, str) and name and not name.startswith('/'), f'Invalid relative path: {name!r}')
    for part in name.split('/'):
        require(part not in ('', '.', '..'), f'Unsafe path component: {name!r}')
        require(not any(ord(c) < 32 or ord(c) == 127 or c in '<>:"\\|?*' for c in part),
                f'Unsupported FAT/Windows filename: {name!r}')
        require(not part.endswith((' ', '.')), f'Filename ends in a space/dot: {name!r}')
        require(len(part.encode('utf-16-le')) // 2 <= 255, f'FAT filename exceeds 255 UTF-16 units: {name!r}')
        stem = part.split('.', 1)[0].upper()
        require(not re.fullmatch(r'CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³]', stem),
                f'Reserved Windows filename: {name!r}')
    return name


def unescape_gnu(name):
    out = []
    index = 0
    escapes = {'\\': '\\', 'n': '\n', 'r': '\r'}
    while index < len(name):
        if name[index] == '\\':
            index += 1
            require(index < len(name) and name[index] in escapes, 'Unsupported GNU checksum filename escape')
            out.append(escapes[name[index]])
        else:
            out.append(name[index])
        index += 1
    return ''.join(out)


def parse_manifest(path):
    regular(path)
    data = path.read_bytes()
    require(data.endswith(b'\n') and b'\x00' not in data, 'Checksum manifest needs newline-delimited GNU records')
    text = data.decode('utf-8', errors='strict')
    entries = {}
    for number, line in enumerate(text.split('\n')[:-1], 1):
        escaped = line.startswith('\\')
        if escaped:
            line = line[1:]
        match = re.fullmatch(r'([0-9a-fA-F]{64}) ([ *])(.+)', line)
        require(match is not None, f'Malformed GNU checksum record at line {number}')
        name = unescape_gnu(match[3]) if escaped else match[3]
        safe_name(name)
        require(name != MANIFEST, 'Checksum manifest cannot include itself')
        require(name not in entries, f'Duplicate checksum path: {name}')
        entries[name] = match[1].lower()
    require(entries, 'Empty checksum manifest')
    return entries


def scan_tree(root):
    require(stat.S_ISDIR(root.lstat().st_mode) and not root.is_symlink(), f'Not a nonsymlink directory: {root}')
    files, directories, folded = {}, set(), {}
    directory_slots = collections.Counter({'': 3})
    def walk_error(error):
        raise VerificationError(f'Cannot inspect payload directory: {error}') from error

    for current, dirnames, filenames in os.walk(root, followlinks=False, onerror=walk_error):
        for basename in sorted(dirnames + filenames):
            path = Path(current) / basename
            name = safe_name(path.relative_to(root).as_posix())
            key = unicodedata.normalize('NFC', name).casefold()
            require(key not in folded, f'Casefold/Unicode path collision: {name} and {folded.get(key)}')
            folded[key] = name
            info = path.lstat()
            parent = path.parent.relative_to(root).as_posix()
            parent = '' if parent == '.' else parent
            directory_slots[parent] += 1 + math.ceil(len(basename.encode('utf-16-le')) / 2 / 13)
            if stat.S_ISDIR(info.st_mode):
                directories.add(name)
                directory_slots[name] += 3
            elif stat.S_ISREG(info.st_mode):
                require(info.st_size < 2**32, f'File exceeds FAT32 limit: {name}')
                files[name] = info.st_size
            else:
                raise VerificationError(f'Symlink or special path is forbidden: {name}')
    require(all(count <= 65534 for count in directory_slots.values()), 'FAT directory entry limit exceeded')
    allocation = sum(((size + CLUSTER_BYTES - 1) // CLUSTER_BYTES) * CLUSTER_BYTES for size in files.values())
    allocation += sum(math.ceil(count * 32 / CLUSTER_BYTES) * CLUSTER_BYTES for count in directory_slots.values())
    require(allocation < 60_000_000_000, 'Cluster-rounded payload exceeds conservative FAT32 capacity bound')
    return files, directories, allocation


def verify_payload(args):
    ready = read_json(args.ready)
    require(ready.get('account_validation') == 'passed', 'Account validation is not passed')
    scope = ready.get('account_validation_scope')
    require(isinstance(scope, str) and scope.strip(), 'Missing prior account-validation scope')
    expected_manifest = sha_value(ready.get('sha256_manifest_sha256'), 'ready manifest')
    expected_driver = sha_value(ready.get('final_driver_manifest_sha256'), 'driver manifest')
    tested = ready.get('tested_file_sha256')
    require(isinstance(tested, dict) and tested, 'Missing tested-file SHA-256 evidence')
    tested = {safe_name(name): sha_value(value, name) for name, value in tested.items()}
    required_tested = {'sources/boot.wim', 'sources/install.swm', 'efi/boot/bootx64.efi',
                       'profiles/local.xml', 'profiles/microsoft.xml', 'MSW11-MEDIA.ID'}
    require(required_tested <= tested.keys(), 'Tested-file evidence lacks required boot/account payloads')
    expected_files = integer(ready.get('payload_files'), 'payload_files')
    expected_bytes = integer(ready.get('payload_bytes'), 'payload_bytes')
    require(digest(args.manifest) == expected_manifest, 'Frozen checksum manifest does not match validation-ready.json')
    entries = parse_manifest(args.manifest)
    files, directories, allocation = scan_tree(args.root)
    expected_names = set(entries) | {MANIFEST}
    require(set(files) == expected_names,
            f'Payload file set differs: missing={sorted(expected_names - files.keys())[:10]}, extra={sorted(files.keys() - expected_names)[:10]}')
    require(len(entries) == expected_files, 'Payload file count differs from validation-ready.json')
    require(sum(files[name] for name in entries) == expected_bytes, 'Payload byte count differs from validation-ready.json')
    require(tested.keys() <= entries.keys(), 'Tested file is absent from checksum manifest')
    require(all(name in tested for name in entries if name.startswith('sources/install') and name.endswith('.swm')),
            'A split installation image lacks tested-file evidence')
    require('Documentation/driver-manifest.json' in entries, 'Driver manifest is missing')
    actual = {}
    for name in sorted(files):
        actual[name] = digest(args.root / name)
        expected = expected_manifest if name == MANIFEST else entries[name]
        require(actual[name] == expected, f'SHA-256 mismatch: {name}')
    require(actual['Documentation/driver-manifest.json'] == expected_driver, 'Final driver manifest changed')
    for name, expected in tested.items():
        require(actual[name] == expected, f'Tested file changed: {name}')
    if args.reference_layout:
        reference = read_json(args.reference_layout)
        require(reference.get('status') == 'passed', 'Reference layout was not verified')
        require(sorted(directories) == reference.get('directories'), 'Readback directory layout differs from source')
    result = {'status': 'passed', 'kind': 'payload', 'root': str(args.root),
              'validation_ready_sha256': digest(args.ready), 'sha256_manifest_sha256': expected_manifest,
              'final_driver_manifest_sha256': expected_driver, 'payload_files': expected_files,
              'payload_bytes': expected_bytes, 'total_files_including_manifest': len(files),
              'total_bytes_including_manifest': sum(files.values()), 'allocation_bound_bytes': allocation,
              'directories': sorted(directories), 'tested_file_sha256': tested,
              'account_validation': 'passed', 'account_validation_scope': scope,
              'account_tests_reexecuted': False}
    write_json(args.report, result)
    print(f'Verified {len(files)} files ({sum(files.values())} bytes), including checksum manifest.')


def geometry(image, partition_only=False):
    require(regular(image).st_size == IMAGE_BYTES, 'Raw image size differs from required geometry')
    with image.open('rb') as stream:
        mbr = stream.read(SECTOR_BYTES)
        require(mbr[510:512] == b'\x55\xaa', 'Missing MBR signature')
        entries = [mbr[446 + index * 16:462 + index * 16] for index in range(4)]
        first = entries[0]
        require(first[0] == 0x80 and first[4] == 0x0c, 'Partition must be active FAT32 LBA (type 0x0c)')
        require(struct.unpack_from('<II', first, 8) == (PARTITION_START, PARTITION_SECTORS), 'Incorrect partition start/size')
        require(all(entry == bytes(16) for entry in entries[1:]), 'Unexpected additional MBR partitions')
        report = {'status': 'passed', 'kind': 'geometry', 'image_bytes': IMAGE_BYTES,
                  'partition_table': 'dos', 'partition_start_sector': PARTITION_START,
                  'partition_sectors': PARTITION_SECTORS, 'partition_type': '0c', 'active': True}
        if partition_only:
            return report
        stream.seek(PARTITION_START * SECTOR_BYTES)
        bpb = stream.read(SECTOR_BYTES)
        require(bpb[510:512] == b'\x55\xaa' and bpb[82:90] == b'FAT32   ', 'Missing FAT32 boot-sector signatures')
        require(struct.unpack_from('<H', bpb, 11)[0] == SECTOR_BYTES and bpb[13] == 64, 'Incorrect FAT sector/cluster sizes')
        require(bpb[71:82] == b'MSW11LENOVO', 'Incorrect FAT volume label')
        require(struct.unpack_from('<I', bpb, 28)[0] == PARTITION_START, 'Incorrect FAT hidden-sector count')
        sectors_per_track, heads = struct.unpack_from('<HH', bpb, 24)
        require((heads, sectors_per_track) == (FAT_HEADS, FAT_SECTORS_PER_TRACK),
                'Incorrect pinned FAT geometry (expected 255 heads / 63 sectors per track)')
        filesystem_sectors = struct.unpack_from('<I', bpb, 32)[0]
        # dosfstools 4.2 mkfs.fat.c:733-735 rounds down to a complete track
        # when alignment is enabled. The builder pins -g 255/63 explicitly.
        # https://github.com/dosfstools/dosfstools/blob/v4.2/src/mkfs.fat.c#L733-L735
        expected_filesystem_sectors = PARTITION_SECTORS // FAT_SECTORS_PER_TRACK * FAT_SECTORS_PER_TRACK
        tail_sectors = PARTITION_SECTORS - filesystem_sectors
        require(0 <= tail_sectors < FAT_SECTORS_PER_TRACK,
                'FAT filesystem overruns the partition or leaves more than a formatter track of unused space')
        require(filesystem_sectors == expected_filesystem_sectors,
                'FAT filesystem sector count does not match exact formatter track rounding')
        require(struct.unpack_from('<H', bpb, 19)[0] == 0, 'Unexpected FAT16 total-sector field')
        require(struct.unpack_from('<H', bpb, 17)[0] == 0 and struct.unpack_from('<H', bpb, 22)[0] == 0, 'Unexpected FAT16 fields')
        require(bpb[16] == 2 and struct.unpack_from('<I', bpb, 36)[0] > 0, 'Invalid FAT32 table geometry')
        require(struct.unpack_from('<H', bpb, 14)[0] >= 32 and struct.unpack_from('<I', bpb, 44)[0] >= 2, 'Invalid FAT32 reserved/root sectors')
        report.update(bytes_per_sector=SECTOR_BYTES, sectors_per_cluster=64,
                      cluster_bytes=CLUSTER_BYTES, filesystem='FAT32', label='MSW11LENOVO',
                      filesystem_sectors=filesystem_sectors, filesystem_bytes=filesystem_sectors * SECTOR_BYTES,
                      partition_tail_sectors=tail_sectors, partition_tail_bytes=tail_sectors * SECTOR_BYTES,
                      heads=heads, sectors_per_track=sectors_per_track,
                      filesystem_sector_alignment='Partition sector count rounded down to a complete 63-sector track')
        return report


def verify_loop(args):
    require(re.fullmatch(r'/dev/loop[0-9]+', args.device), 'Refusing a non-loop device')
    require(stat.S_ISBLK(os.stat(args.device).st_mode), 'Allocated loop path is not a block device')
    data = read_json(args.metadata).get('loopdevices')
    require(isinstance(data, list) and len(data) == 1, 'Expected one allocated loop device')
    loop = data[0]
    require(loop.get('name') == args.device, 'Loop metadata names a different device')
    require(Path(loop.get('back-file', '')).resolve() == args.image.resolve(), 'Loop backing file differs from created image')
    require(int(loop.get('back-ino', -1)) == regular(args.image).st_ino, 'Loop backing inode differs from created image')
    require(loop.get('offset') == 0 and loop.get('sizelimit') == 0, 'Unexpected loop offset or size limit')
    require(loop.get('log-sec') == SECTOR_BYTES, 'Loop logical sector size is not 512')
    require(loop.get('ro') is args.read_only, 'Loop read-only state differs from requested mode')
    require(regular(args.image).st_size == IMAGE_BYTES, 'Loop backing image has wrong size')
    print(f'Verified loop backing and access mode: {args.device}')


def release(args):
    """Internal publication step; the builder is responsible for fsck and read-only attachment."""
    source = read_json(args.source_report)
    readback = read_json(args.readback_report)
    require(source.get('status') == readback.get('status') == 'passed', 'Payload verification did not pass')
    for key in ('validation_ready_sha256', 'sha256_manifest_sha256', 'final_driver_manifest_sha256',
                'payload_files', 'payload_bytes', 'directories', 'tested_file_sha256'):
        require(source.get(key) == readback.get(key), f'Source/readback reports differ: {key}')
    require(digest(args.ready) == source.get('validation_ready_sha256'), 'Ready evidence changed after verification')
    require(regular(args.fsck_log).st_size > 0, 'Missing filesystem-check output')
    shape = geometry(args.image)
    print('Hashing the entire detached raw image...', flush=True)
    image_sha = digest(args.image)
    report = {'status': 'verified', 'created_at_utc': datetime.now(timezone.utc).isoformat(),
              'image': PUBLIC_IMAGE, 'image_format': 'raw', 'image_bytes': IMAGE_BYTES, 'image_sha256': image_sha,
              'source_validation_ready_sha256': source['validation_ready_sha256'],
              'source_sha256_manifest_sha256': source['sha256_manifest_sha256'],
              'source_driver_manifest_sha256': source['final_driver_manifest_sha256'],
              'payload_files': source['payload_files'], 'payload_bytes': source['payload_bytes'],
              'total_files_including_manifest': source['total_files_including_manifest'],
              'total_bytes_including_manifest': source['total_bytes_including_manifest'],
              'geometry': shape, 'source_payload_verification': 'passed', 'read_only_readback_verification': 'passed',
              'filesystem_check': 'fsck.vfat -n passed before detach',
              'filesystem_check_log_sha256': digest(args.fsck_log),
              'verification_record_source': 'Completed-step records supplied by build-release-image.sh; the internal publication step checks report consistency and hashes the image, but does not independently rerun filesystem checking or read-only attachment.',
              'account_validation': source['account_validation'], 'account_validation_scope': source['account_validation_scope'],
              'account_tests_reexecuted': False, 'boot_smoke_test_performed': False,
              'physical_device_functionality_tested': False,
              'validation_scope': 'Frozen staged payload and existing account-test evidence verified; image copied, reopened read-only, fully read back, filesystem checked, geometry checked, and entire raw file hashed. No image boot or physical-device functionality test is claimed.'}
    write_json(args.report, report)
    with args.checksum.open('x', encoding='ascii') as stream:
        stream.write(f'{image_sha}  {PUBLIC_IMAGE}\n')
        stream.flush()
        os.fsync(stream.fileno())
    print(f'Complete image SHA-256: {image_sha}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('payload', help='Check exact payload set, FAT names/limits, hashes, and ready evidence')
    for name in ('root', 'ready', 'manifest', 'report'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--reference-layout', type=Path)
    p.set_defaults(function=verify_payload)
    p = sub.add_parser('geometry', help='Check a regular raw image MBR and FAT32 BPB')
    p.add_argument('--image', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--partition-only', action='store_true')
    p.set_defaults(function=lambda a: write_json(a.report, geometry(a.image, a.partition_only)))
    p = sub.add_parser('loop', help='Check captured losetup JSON against the created regular image')
    for name in ('image', 'metadata'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--device', required=True)
    p.add_argument('--read-only', action='store_true')
    p.set_defaults(function=verify_loop)
    p = sub.add_parser('release', help='Internal builder publication step; consumes completed-step records and hashes the detached image')
    for name in ('image', 'ready', 'source-report', 'readback-report', 'fsck-log', 'report', 'checksum'):
        p.add_argument('--' + name, type=Path, required=True)
    p.set_defaults(function=release)
    args = parser.parse_args()
    try:
        args.function(args)
    except (VerificationError, OSError, ValueError, KeyError, TypeError, struct.error) as error:
        print(f'Verification failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
