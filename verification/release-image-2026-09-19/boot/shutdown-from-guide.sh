set -euo pipefail
release_dir="$PWD/release/r3"
smoke_dir="$PWD/verification/r3"
set -euo pipefail
smoke_pid=$(cat "$smoke_dir/qemu.pid")
[[ "$smoke_pid" =~ ^[0-9]+$ ]]
/usr/bin/python3 scripts/qmp.py "$smoke_dir/qmp.sock" type $'4\n'
for attempt in {1..60}; do
  if ! test -S "$smoke_dir/qmp.sock" && ! kill -0 "$smoke_pid" 2>/dev/null; then break; fi
  sleep 1
done
test ! -S "$smoke_dir/qmp.sock"
if kill -0 "$smoke_pid" 2>/dev/null; then
  printf 'VM process has not exited; inspect it before continuing.\n' >&2
  exit 1
fi
(cd "$release_dir" && sha256sum -c MSW11-Lenovo-x64.img.sha256)
