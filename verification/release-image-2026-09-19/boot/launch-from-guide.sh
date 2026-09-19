set -euo pipefail
release_dir="$PWD/release/r3"
smoke_dir="$PWD/verification/r3"
image_path="$release_dir/MSW11-Lenovo-x64.img"
test -f "$image_path"
test ! -L "$image_path"
SMOKE_DIR="$smoke_dir" python3 - <<'PY'
from pathlib import Path
import os
p = Path(os.environ['SMOKE_DIR']).resolve()/'qmp.sock'
if len(os.fsencode(p)) > 107:
    raise SystemExit('Choose a shorter actual smoke directory')
PY
mkdir "$smoke_dir"
cp /usr/share/OVMF/OVMF_VARS_4M.ms.fd "$smoke_dir/vars.fd"
qemu-system-x86_64 -name MSW11-release-image-smoke \
  -enable-kvm -machine q35,smm=on -cpu host -smp 2 -m 4096 \
  -no-user-config -nodefaults -nic none -serial none -parallel none \
  -global driver=cfi.pflash01,property=secure,value=on \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.ms.fd \
  -drive "if=pflash,format=raw,file=$smoke_dir/vars.fd" \
  -drive "if=none,id=installer,format=raw,readonly=on,file=$image_path" \
  -device qemu-xhci,id=usb \
  -device usb-storage,drive=installer,removable=on,bootindex=1 \
  -device usb-kbd -device usb-tablet -vga std -boot strict=on \
  -display none -qmp "unix:$smoke_dir/qmp.sock,server=on,wait=off" \
  -pidfile "$smoke_dir/qemu.pid" -S -daemonize
/usr/bin/python3 scripts/qmp.py "$smoke_dir/qmp.sock" execute \
  '{"command":"query-named-block-nodes"}' > "$smoke_dir/block-graph-before-boot.txt"
