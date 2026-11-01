#include "gamescope-control-client-protocol.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wayland-client.h>
static struct gamescope_control *control;
static int done;
static void feature(void *d, struct gamescope_control *c, uint32_t a, uint32_t b, uint32_t f) {}
static void info(void *d, struct gamescope_control *c, const char *a, const char *b, const char *f,
                 uint32_t flags, struct wl_array *r) {}
static void taken(void *d, struct gamescope_control *c, const char *path) {
    puts(path);
    done = 1;
}
static const struct gamescope_control_listener ctl_listener = {
    .feature_support = feature, .active_display_info = info, .screenshot_taken = taken};
static void global(void *d, struct wl_registry *r, uint32_t name, const char *iface,
                   uint32_t version) {
    if (!strcmp(iface, "gamescope_control")) {
        control = wl_registry_bind(r, name, &gamescope_control_interface, 3);
        gamescope_control_add_listener(control, &ctl_listener, 0);
    }
}
static void removed(void *d, struct wl_registry *r, uint32_t name) {}
static const struct wl_registry_listener registry_listener = {global, removed};
int main(int argc, char **argv) {
    if (argc < 2)
        return 2;
    struct wl_display *display = wl_display_connect(getenv("GAMESCOPE_WAYLAND_DISPLAY"));
    if (!display)
        return 3;
    struct wl_registry *r = wl_display_get_registry(display);
    wl_registry_add_listener(r, &registry_listener, 0);
    wl_display_roundtrip(display);
    wl_display_roundtrip(display);
    if (!control)
        return 4;
    gamescope_control_take_screenshot(control, argv[1], 3, 0);
    while (!done && wl_display_dispatch(display) >= 0) {
    }
    wl_display_disconnect(display);
    return !done;
}
