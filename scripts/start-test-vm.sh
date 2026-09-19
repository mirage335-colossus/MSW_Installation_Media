#!/bin/bash
set -euo pipefail
base=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
test_name=${1:?Specify local or cloud}
case "$test_name" in local|cloud) ;; *) exit 2;; esac
test_dir="$base/verification/$test_name"
test_media="$base/verification/test-usb.img"
test -f "$test_media"
test -f "$test_dir/system.qcow2"
test ! -S "$test_dir/qmp.sock"
swtpm socket --tpm2 --tpmstate "dir=$test_dir/tpm" \
  --ctrl "type=unixio,path=$test_dir/tpm.sock" \
  --pid "file=$test_dir/tpm.pid" --daemon
netargs=(-nic none)
if [ "$test_name" = cloud ]; then
  netargs=(-netdev user,id=net0 -device e1000e,netdev=net0)
fi
qemu-system-x86_64 -name "MSW11-$test_name-verification" \
  -enable-kvm -machine q35,smm=on -cpu host -smp 4 -m 6144 \
  -global driver=cfi.pflash01,property=secure,value=on \
  -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.ms.fd \
  -drive "if=pflash,format=raw,file=$test_dir/vars.fd" \
  -chardev "socket,id=chrtpm,path=$test_dir/tpm.sock" \
  -tpmdev emulator,id=tpm0,chardev=chrtpm -device tpm-tis,tpmdev=tpm0 \
  -drive "file=$test_dir/system.qcow2,format=qcow2,if=none,id=system" \
  -device ide-hd,drive=system,bootindex=2 \
  -device qemu-xhci,id=usb \
  -drive "file=$test_media,format=raw,readonly=on,if=none,id=installer" \
  -device usb-storage,id=installer-usb,drive=installer,removable=on,bootindex=1 \
  -device usb-tablet -vga std "${netargs[@]}" \
  -display none -qmp "unix:$test_dir/qmp.sock,server=on,wait=off" \
  -pidfile "$test_dir/qemu.pid" -D "$test_dir/qemu.log" -daemonize
printf 'Started isolated %s verification VM.\n' "$test_name"
