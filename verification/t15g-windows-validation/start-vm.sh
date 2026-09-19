#!/bin/bash
set -euo pipefail
base=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
vm_dir="$base/verification/local"
check_dir="$base/verification/t15g-windows-validation"
test -f "$vm_dir/system.qcow2"
test -f "$vm_dir/vars.fd"
test -f "$vm_dir/tpm/tpm2-00.permall"
test ! -S "$check_dir/qmp.sock"
swtpm socket --tpm2 --tpmstate "dir=$vm_dir/tpm" --ctrl "type=unixio,path=$check_dir/tpm.sock" --pid "file=$check_dir/tpm.pid" --daemon
qemu-system-x86_64 -name MSW11-T15g-driver-validation \
 -enable-kvm -machine q35,smm=on -cpu host -smp 4 -m 6144 \
 -global driver=cfi.pflash01,property=secure,value=on \
 -drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.ms.fd \
 -drive "if=pflash,format=raw,file=$vm_dir/vars.fd" \
 -chardev "socket,id=chrtpm,path=$check_dir/tpm.sock" \
 -tpmdev emulator,id=tpm0,chardev=chrtpm -device tpm-tis,tpmdev=tpm0 \
 -drive "file=$vm_dir/system.qcow2,format=qcow2,if=none,id=system" \
 -device ide-hd,drive=system,bootindex=1 \
 -device qemu-xhci,id=usb \
 -drive "file=$check_dir/input.img,format=raw,readonly=on,if=none,id=input" \
 -device usb-storage,id=driver-input,drive=input,removable=on \
 -drive "file=$check_dir/output.img,format=raw,if=none,id=output" \
 -device usb-storage,id=log-output,drive=output,removable=on \
 -device usb-tablet -vga std -nic none -display none \
 -qmp "unix:$check_dir/qmp.sock,server=on,wait=off" \
 -pidfile "$check_dir/qemu.pid" -D "$check_dir/qemu.log" -daemonize
