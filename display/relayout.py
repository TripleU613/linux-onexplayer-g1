#!/usr/bin/env python3
# Re-pin a GNOME (Wayland) multi-monitor layout when a connector name changed
# (e.g. DP-2 -> DP-3) and the cursor starts "leaking" onto the wrong screen.
# Edit LAYOUT, then run. Applies live AND persists to ~/.config/monitors.xml.
#
# Each row: (connector, x, y, scale, primary). Get connector names from
# Settings > Displays, or this returns "not connected" if wrong.
import gi
from gi.repository import Gio, GLib

LAYOUT = [
    ("DP-3",  0,    0,    1.0, True),   # external monitor on top, primary
    ("eDP-1", 2048, 1440, 2.5, False),  # handheld centered directly below
]

D = ("org.gnome.Mutter.DisplayConfig", "/org/gnome/Mutter/DisplayConfig",
     "org.gnome.Mutter.DisplayConfig")
bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
serial, monitors, _logical, _props = bus.call_sync(
    *D, "GetCurrentState", None, None, Gio.DBusCallFlags.NONE, -1, None).unpack()

def current_mode(conn):
    for spec, modes, _mp in monitors:
        if spec[0] == conn:
            for m in modes:
                if m[6].get("is-current"):
                    return m[0]
            return modes[0][0]
    raise SystemExit(f"connector {conn} not connected")

logical = [(x, y, scale, 0, prim, [(conn, current_mode(conn), {})])
           for conn, x, y, scale, prim in LAYOUT]
params = GLib.Variant("(uua(iiduba(ssa{sv}))a{sv})", (serial, 2, logical, {}))  # 2 = persistent
bus.call_sync(*D, "ApplyMonitorsConfig", params, None, Gio.DBusCallFlags.NONE, -1, None)
print("applied + saved to ~/.config/monitors.xml")
