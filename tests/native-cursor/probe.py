import ctypes as c, os, time, subprocess
import ctypes.util
from pathlib import Path

os.environ["SDL_VIDEO_DRIVER"] = "wayland"
os.environ["SDL_VIDEO_WAYLAND_ALLOW_LIBDECOR"] = "0"
library = os.environ.get("SDL3_LIBRARY") or ctypes.util.find_library("SDL3")
if not library:
    raise SystemExit("SDL3 not found; set SDL3_LIBRARY to its shared library path")
s = c.CDLL(library)
ctl = os.environ.get("GAMESCOPECTL", "gamescopectl")
output = Path(os.environ.get("CURSOR_PROBE_OUTPUT", ".")).resolve()


def bind(name, restype, args):
    f = getattr(s, name)
    f.restype = restype
    f.argtypes = args
    return f


init = bind("SDL_Init", c.c_bool, [c.c_uint])
err = bind("SDL_GetError", c.c_char_p, [])
window = bind(
    "SDL_CreateWindow", c.c_void_p, [c.c_char_p, c.c_int, c.c_int, c.c_uint64]
)
renderer = bind("SDL_CreateRenderer", c.c_void_p, [c.c_void_p, c.c_char_p])
color = bind(
    "SDL_SetRenderDrawColor",
    c.c_bool,
    [c.c_void_p, c.c_uint8, c.c_uint8, c.c_uint8, c.c_uint8],
)
clear = bind("SDL_RenderClear", c.c_bool, [c.c_void_p])
present = bind("SDL_RenderPresent", c.c_bool, [c.c_void_p])
poll = bind("SDL_PollEvent", c.c_bool, [c.c_void_p])
show = bind("SDL_ShowCursor", c.c_bool, [])
hide = bind("SDL_HideCursor", c.c_bool, [])
create = bind("SDL_CreateSystemCursor", c.c_void_p, [c.c_int])
setcursor = bind("SDL_SetCursor", c.c_bool, [c.c_void_p])
quit = bind("SDL_Quit", None, [])
assert init(0x20), err()
w = window(b"Native Wayland cursor probe", 640, 480, 0)
assert w, err()
r = renderer(w, None)
assert r, err()
cursor = create(0)
assert cursor, err()
assert setcursor(cursor), err()
assert show(), err()
event = c.create_string_buffer(128)
start = time.monotonic()
state = -1
captured = set()
if os.environ.get("CURSOR_PROBE_CAPTURE"):
    subprocess.run([ctl, "native_cursor_debug", "1"], check=True)
while time.monotonic() - start < 24:
    while poll(event):
        pass
    phase = int((time.monotonic() - start) // 6)
    if phase != state:
        state = phase
        if phase == 1:
            hide()
        else:
            show()
        if phase == 2:
            other = create(2)
            assert other, err()
            assert setcursor(other), err()
        print("CURSOR_PHASE", phase, "hidden" if phase == 1 else "visible", flush=True)
    color(r, 20, 80 if phase != 1 else 20, 100, 255)
    clear(r)
    present(r)
    if (
        os.environ.get("CURSOR_PROBE_CAPTURE")
        and phase not in captured
        and time.monotonic() - start - phase * 6 > 2
    ):
        captured.add(phase)
        path = str(output / f"headless-phase{phase}.png")
        subprocess.run(
            [ctl, "native_cursor_warp", f"{100 + phase * 120},{100 + phase * 80}"],
            check=True,
        )
        time.sleep(0.1)
        subprocess.run([os.environ["CURSOR_PROBE_CAPTURE"], path], check=True)
    time.sleep(0.016)
quit()
print("PROBE_COMPLETED", flush=True)
