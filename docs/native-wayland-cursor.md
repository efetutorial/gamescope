# Native Wayland cursors in Gamescope 3.17.0

This fork adds cursor support for native Wayland clients launched with
`--expose-wayland`. It was developed and tested with native Linux CS2 on a Niri
Wayland session, including 1920×1440 stretched to 2560×1440 at 240 Hz.

## What it fixes

Gamescope's XDG focus path previously logged `NO CURSOR IMPL XDG`. The patch
handles `wl_pointer.set_cursor`, copies cursor buffer pixels under the Wayland
server lock, and uploads them on the compositor thread. It tracks cursor surface
commits, hide requests, hotspots, focus changes, and surface/seat destruction.

Positioning uses the logical Wayland surface dimensions. The XDG window geometry
on this path can be 0×0: dividing by it produced infinite offsets, a cursor stuck
at the top left, or no visible cursor during full composition.

## Build and run

Build the fork using the [upstream instructions](../README.md#building). The
starting revision is Gamescope 3.17.0 (`e6674a98118ca7b098b98a3874b8f195ae1bf750`).
This branch is a focused prototype against that release, not a complete Wayland
cursor implementation for every client or backend.

For CS2, point Steam's launch options at the built Gamescope executable:

```sh
/path/to/gamescope -w 1920 -h 1440 -W 2560 -H 1440 -S stretch -f -r 240 --force-grab-cursor --expose-wayland -- env SDL_VIDEO_DRIVER=wayland SDL_VIDEO_WAYLAND_ALLOW_LIBDECOR=0 %command%
```

Adjust the resolution and refresh rate for your display. The SDL libdecor setting
worked around an `invalid xdg-surface geometry` disconnect in the tested setup;
it does not require editing CS2's game files.

Steam Overlay input needs the separate
[Gamescope overlay bridge fix](https://github.com/efetutorial/ge-steam-overlay-wayland/tree/fix/gamescope-overlay-input).
The game remains a native Wayland client; Gamescope still has its internal
XWayland server.

## Supported cursor buffers

- CPU-readable ARGB8888, XRGB8888, ABGR8888, and XBGR8888 buffers.
- Normal buffer transform, including buffer scale; logical dimensions up to
  1024×1024.
- Application hide/show requests and cursor image changes.

Rotated cursor transforms and cursor buffers that cannot be CPU-mapped are not
implemented. Other compositors, GPU configurations, and multi-seat behavior have
not been validated. Existing X11 clients continue to use the XFixes cursor path.

## Integration test

Requires Python 3, SDL3, a C compiler, `pkg-config`, Wayland client headers,
`wayland-scanner`, and a working Vulkan driver. It creates a separate headless
Gamescope instance, not a window in the current game session.

```sh
GAMESCOPE_BINARY=/path/to/build/src/gamescope \
SDL3_LIBRARY=/path/to/libSDL3.so.0 \
./tests/native-cursor/run.sh
```

`SDL3_LIBRARY` can be omitted when the shared library is discoverable normally.
The test shows, hides, changes, and moves an SDL cursor. It captures Gamescope's
full composition and checks the actual PNG pixels for movement and for the
hidden cursor's absence. The previous zero-geometry implementation failed this
test; the fixed build passed it. CS2 menu movement was also confirmed manually.

`GAMESCOPE_DEBUG_NATIVE_CURSOR=1` enables diagnostics and the debug-only
`native_cursor_warp x,y` command used by this test. `gamescopectl
native_cursor_debug 1` enables runtime logging, and `0` disables it. These controls
are for development; normal launches do not need them.
