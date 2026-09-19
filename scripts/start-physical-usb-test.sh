#!/bin/bash
# Start only after write-verified-usb.sh completes. No installation destination
# is attached. The fixed physical USB is read-only at both block graph layers.
set -euo pipefail
umask 077
if (($# != 0)); then
  printf 'This launcher accepts no device or VM arguments.\n' >&2
  exit 2
fi
if ((EUID != 0)); then
  printf 'Run with sudo -n bash scripts/start-physical-usb-test.sh after USB verification.\n' >&2
  exit 2
fi
base=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
readonly target=/dev/disk/by-id/usb-Kingston_DataTraveler_3.0_4CEDFB74A32C1A70790301C3-0:0
readonly test_dir="$base/verification/physical-boot"
readonly firmware=/usr/share/OVMF/OVMF_CODE_4M.ms.fd
readonly vars_template=/usr/share/OVMF/OVMF_VARS_4M.ms.fd
test -r "$firmware"
test -r "$vars_template"
test -c /dev/kvm
test -s "$base/verification/usb-readback-sha256.txt"
test -s "$base/verification/usb-filesystem-check.txt"
test -s "$base/verification/usb-final-partition-table.txt"
command -v qemu-system-x86_64 >/dev/null

# --tree is necessary: PATH without NAME otherwise flattens lsblk JSON here.
python3 - "$target" <<'PY'
import json, os, stat, subprocess, sys
target = sys.argv[1]
assert stat.S_ISBLK(os.stat(target).st_mode), 'Fixed USB target is not a block device'
devices = json.loads(subprocess.check_output([
    'lsblk', '--tree', '-b', '-J', '-o',
    'PATH,SIZE,MODEL,SERIAL,TRAN,RM,TYPE,MOUNTPOINTS', target
]))['blockdevices']
assert len(devices) == 1, 'Unexpected target topology'
d = devices[0]
assert d['serial'] == '4CEDFB74A32C1A70790301C3', 'USB serial mismatch'
assert d['size'] == 61991813120, 'USB capacity mismatch'
assert d['type'] == 'disk' and d['tran'] == 'usb' and d['rm'] is True
assert d['model'].strip() == 'DataTraveler 3.0', 'USB model mismatch'
def unmounted(node):
    assert not any(node.get('mountpoints') or []), 'USB or child partition is mounted'
    for child in node.get('children', []):
        unmounted(child)
unmounted(d)
assert os.path.realpath(target) == d['path'], 'USB identity changed'
assert len(d.get('children', [])) == 1, 'Expected exactly one USB partition'
print('Verified physical USB, to be opened read-only:', d['path'], d['serial'])
PY

# Atomic mkdir deliberately refuses every existing test directory, including
# previous firmware variables, logs, PID files, sockets, or symlinks.
if ! mkdir -- "$test_dir"; then
  printf 'Refusing to overwrite existing physical-boot test artifacts.\n' >&2
  exit 1
fi
cp --no-clobber -- "$vars_template" "$test_dir/vars.fd"
sha256sum "$firmware" "$vars_template" "$test_dir/vars.fd" > "$test_dir/firmware-start-sha256.txt"

# Pause the CPUs until QMP confirms the exact USB backends are read-only.
# -nodefaults prevents implicit disks/NICs. Only firmware flash and the fixed
# USB exist in the block graph. No host internal drive or guest system disk.
qemu-system-x86_64 -name MSW11-physical-USB-readonly-smoke-test \
  -enable-kvm -machine q35,smm=on -cpu host -smp 2 -m 4096 \
  -no-user-config -nodefaults -nic none -serial none -parallel none \
  -global driver=cfi.pflash01,property=secure,value=on \
  -drive "if=pflash,format=raw,readonly=on,file=$firmware" \
  -drive "if=pflash,format=raw,file=$test_dir/vars.fd" \
  -blockdev "driver=host_device,node-name=physical_usb_host,filename=$target,read-only=on" \
  -blockdev driver=raw,node-name=physical_usb,file=physical_usb_host,read-only=on \
  -device qemu-xhci,id=usb \
  -device usb-storage,id=physical-installer,drive=physical_usb,removable=on,bootindex=1 \
  -device usb-kbd -device usb-tablet -vga std -boot strict=on \
  -display none -qmp "unix:$test_dir/qmp.sock,server=on,wait=off" \
  -pidfile "$test_dir/qemu.pid" -D "$test_dir/qemu.log" -S -daemonize

python3 - "$test_dir" "$target" "$firmware" <<'PY'
import json, os, socket, sys
from pathlib import Path
test_dir, target, firmware = sys.argv[1:]
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.settimeout(10)
s.connect(test_dir + '/qmp.sock')
f = s.makefile('rwb', buffering=0)
def receive():
    while True:
        line = f.readline()
        if not line:
            raise RuntimeError('QMP closed unexpectedly')
        result = json.loads(line)
        if 'event' not in result:
            return result
def execute(command):
    f.write((json.dumps({'execute': command}) + '\n').encode())
    result = receive()
    if 'error' in result:
        raise RuntimeError(result['error'])
    return result.get('return')
receive()
execute('qmp_capabilities')
try:
    nodes = execute('query-named-block-nodes')
    blocks = execute('query-block')
    Path(test_dir, 'block-graph-before-boot.json').write_text(
        json.dumps({'nodes': nodes, 'blocks': blocks}, indent=2) + '\n')
    allowed_files = {
        os.path.realpath(target), os.path.realpath(firmware),
        os.path.realpath(test_dir + '/vars.fd')
    }
    for node in nodes:
        assert os.path.realpath(node['file']) in allowed_files, 'Unexpected block storage attached'
    for name in ('physical_usb_host', 'physical_usb'):
        matched = [n for n in nodes if n.get('node-name') == name]
        assert len(matched) == 1, 'Missing or duplicate physical USB backend'
        assert matched[0]['ro'] is True, 'Physical USB is not read-only'
        assert os.path.realpath(matched[0]['file']) == os.path.realpath(target)
    assert sum(1 for b in blocks if b.get('inserted', {}).get('node-name') == 'physical_usb') == 1
    execute('cont')
except BaseException:
    try:
        execute('quit')
    except Exception:
        pass
    raise
finally:
    f.close()
    s.close()
print('Started physical USB boot smoke test with no network or installation destination.')
print('QMP:', test_dir + '/qmp.sock')
print('Use sudo with scripts/qmp.py to capture the menu and quit this root-owned test VM.')
PY
