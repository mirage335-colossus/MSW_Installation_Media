#!/bin/bash
set -euo pipefail
base=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
image_path="$base/verification/test-usb.img"
mount_path="$base/verification/test-usb-mount"
test -f "$base/staging/sources/install.swm"
test -f "$base/staging/efi/boot/bootx64.efi"
test ! -e "$image_path"
mkdir -p "$mount_path"
truncate -s 61991813120 "$image_path"
printf 'label: dos\nunit: sectors\n\nstart=2048, type=c, bootable\n' | /usr/sbin/sfdisk "$image_path"
loop_device=$(sudo -n losetup --find --show --partscan "$image_path")
cleanup() {
  if mountpoint -q "$mount_path"; then sudo -n umount "$mount_path"; fi
  sudo -n losetup -d "$loop_device"
}
trap cleanup EXIT
sudo -n mkfs.vfat -F 32 -s 64 -n MSW11LENOVO "${loop_device}p1"
sudo -n mount -o "uid=$(id -u),gid=$(id -g),umask=022,nosuid,nodev,noexec" "${loop_device}p1" "$mount_path"
rsync -rt --info=stats2 "$base/staging/" "$mount_path/"
sync -f "$mount_path"
printf 'Boot test image prepared.\n'
