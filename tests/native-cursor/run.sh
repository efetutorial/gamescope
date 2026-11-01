#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
gamescope_bin=${GAMESCOPE_BINARY:-"$repo_root/build/src/gamescope"}
gamescope_bin=$(realpath "$gamescope_bin")
probe_dir=$(mktemp -d)
trap 'rm -rf -- "$probe_dir"' EXIT
wayland-scanner client-header "$repo_root/protocol/gamescope-control.xml" "$probe_dir/gamescope-control-client-protocol.h"
wayland-scanner private-code "$repo_root/protocol/gamescope-control.xml" "$probe_dir/gamescope-control-protocol.c"
read -r -a cflags <<< "$(pkg-config --cflags wayland-client)"
read -r -a libs <<< "$(pkg-config --libs wayland-client)"
"${CC:-cc}" "${cflags[@]}" -I"$probe_dir" "$repo_root/tests/native-cursor/capture.c" "$probe_dir/gamescope-control-protocol.c" "${libs[@]}" -o "$probe_dir/capture"
export CURSOR_PROBE_OUTPUT="$probe_dir"
GAMESCOPE_DEBUG_NATIVE_CURSOR=1 "$gamescope_bin" --backend headless \
    -w 640 -h 480 -W 960 -H 720 --force-grab-cursor --expose-wayland -- \
    env CURSOR_PROBE_CAPTURE="$probe_dir/capture" \
    GAMESCOPECTL="$(dirname "$gamescope_bin")/gamescopectl" \
    python3 "$repo_root/tests/native-cursor/probe.py"
python3 "$repo_root/tests/native-cursor/verify.py"
