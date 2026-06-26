# linux-onexplayer-g1

Linux fixes for the OneXPlayer G1 A (Ryzen AI 9 HX 370), tested on Ubuntu 26.04 (Wayland/GNOME, Python 3.14).

## 1. Auto-rotate stuck flipping to portrait
`bmi260` accelerometer is mounted 180° vs the panel, so `iio-sensor-proxy` reads landscape as `bottom-up`.
```sh
sudo cp autorotate/61-sensor-local.hwdb /etc/udev/hwdb.d/
sudo systemd-hwdb update
sudo udevadm trigger -p DEVNAME=/dev/iio:device0
sudo systemctl restart iio-sensor-proxy
```

## 2. FocalTech FT9366 fingerprint (USB 2808:c652) unsupported
No vendor Linux driver. The community FT9366 shim driver already lists `c652`.
```sh
# driver + libgusb shim:  https://github.com/leopalladium/focaltech-ft9366-arch-shim
sudo cp fingerprint/80-focaltech-c652.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
sudo systemctl restart fprintd
fprintd-enroll          # FT9366 is sleepy: firm press-and-hold, ~6-8 presses
sudo apt-mark hold libfprint-2-2   # keep updates from overwriting the driver
```

## 3. Face unlock (Howdy) on the IR camera
The G1 has an IR cam (`GREY` format, `/dev/video2`). Three G1-specific fixes (see `faceid/patch-howdy.sh`):
`pam.py` ships Python-2 code (won't load -> silent fallback); pin the camera by stable `by-path` and force OpenCV's V4L2 backend; rotate IR frames 90° (cam mounted rotated).
```sh
# install Howdy, then build dlib for Python 3.14:  pip wheel dlib
sudo faceid/patch-howdy.sh
sudo howdy -U "$USER" add
sudo pam-auth-update --enable howdy
```

## 4. Screen stuck below max brightness
GNOME auto-brightness dims off the `bmi260` (an IMU, not a light sensor).
```sh
brightness/disable-auto-brightness.sh
```

## 5. GDM shows a "GDM Greeter" lock screen, no user list
On GNOME 50 the greeter launched a full `ubuntu` desktop (`gnome-shell --mode=ubuntu`) instead of the login screen, because `/etc/dconf/profile/gdm` was missing its `file-db` line (so `session-name=gnome-login` never loaded) and the per-seat state had a saved `ubuntu` session pinning it. Reinstalling `gdm3` does **not** fix it — that profile is generated at runtime, not shipped by the package.
```sh
sudo greeter/fix-gdm-greeter.sh
# greeter then runs `gnome-shell --mode=gdm` and lists your user
```

## 6. USB peripherals on the internal hub flap / `error -71` (partial)
The G1's internal hub (QinHeng `1a86:8091`) and passive hubs (Genesys `05e3:0610`) are power-marginal — hot-plugged receivers `attempt power cycle` / `error -71` and drag siblings (incl. the built-in keyboard) offline.

What helps — add to `GRUB_CMDLINE_LINUX_DEFAULT`, then `sudo update-grub`:
```sh
usbcore.autosuspend=-1 usbcore.old_scheme_first=1 usbcore.quirks=05e3:0610:ej,1ea7:0002:e usbhid.quirks=0x05e3:0x0610:0x04
```
Plus a boot service that forces every USB port to stay powered (runs `Before=gdm`), and a udev rule keeping hubs powered:
```sh
sudo cp usb/usb-hub-poweron.sh /usr/local/bin/ && sudo chmod +x /usr/local/bin/usb-hub-poweron.sh
sudo cp usb/usb-hub-poweron.service /etc/systemd/system/ && sudo systemctl enable usb-hub-poweron
sudo cp usb/99-usb-autosuspend.rules /etc/udev/rules.d/ && sudo udevadm control --reload-rules
```
Bare low-power receivers then work in a strong port. **Combo (keyboard+mouse+speaker) receivers have an internal hub + amp → too much draw for a bare port; use a powered hub.** **Still open:** a 2.4 GHz receiver that works at the greeter goes dead in-session after login (greeter↔session device-handoff race) — not yet root-caused.
## 7. External monitor: cursor "leaks" to it / saved layout not restoring
GNOME keys its multi-monitor layout (`~/.config/monitors.xml`) by **connector name**
(e.g. `DP-2`). If the port/connector changes (`DP-2` -> `DP-3` after a replug/reboot),
the saved layout stops matching and GNOME auto-arranges badly — the small handheld
screen lands at the top-left of the big monitor, so the cursor spills onto the monitor
from the handheld's top-right edge.

Fix: re-arrange once in **Settings > Displays** (GNOME re-saves for the new connector),
or run `display/relayout.py` (edit the connectors/positions inside first) to apply and
persist a layout from the CLI.

## 8. Controller RGB (HHD detects it but never lights it)
[Handheld Daemon](https://github.com/hhd-dev/hhd) (`hhd@user`) drives the G1 A controller, but RGB has **two** bugs on this device:

**(a) Controller won't start → RGB plugin never runs.** HHD's G1 profile hard-requires the detachable keyboard's touchpad interface (`6080:8060`). When it isn't attached, HHD loops *"controllers disconnected, restarting after 3s"* forever and never starts the `controller_rgb` plugin. Make that device optional in `hhd/device/oxp/base.py` — the `GenericGamepadEvdev` block commented `# Touchpad keyboard` (`vid=[0x6080], pid=[0x8060]`): set `required=False` and `requires_start=False`, then `sudo systemctl restart hhd@$USER`. (Lives in HHD's package → re-apply after HHD updates.)

**(b) Even running, HHD never writes the RGB bytes.** It logs `Setting RGB…` but the actual device write (`OXP C: …` in `hid_v1.py`) never fires — nothing reaches `/dev/hidraw1`. Workaround: write the OXP vendor command straight to the device (format reverse-engineered from `hhd/device/oxp/hid_v1.py`):
```sh
sudo cp rgb/oxp-rgb.py /usr/local/bin/ && sudo chmod +x /usr/local/bin/oxp-rgb.py
sudo cp rgb/oxp-rgb.conf /etc/oxp-rgb.conf       # mode=effect|solid; effect=aurora/flowing/neon/cyberpunk/...; or r/g/b
sudo cp rgb/oxp-rgb.service /etc/systemd/system/ && sudo systemctl enable --now oxp-rgb
```
Self-contained (no HHD import), finds the hidraw by VID:PID `1a2c:b001`, runs alongside HHD (concurrent hidraw write is fine). Sides: `1`=left stick, `2`=right stick, `3`=center V, `4`=touch-kbd, `5`=front triangle.

## 9. Mouse↔keypad toggle on the keyboard pops up GNOME Settings
The detachable keyboard's touchpad (AMIRA-KEYBOAR, USB `6080:8060`) emits `F13`/`F14`/`F17` when you toggle it between **mouse** and **keypad** mode. `F17` matches GNOME's Settings launcher, so every switch-to-keypad opens the Settings app. The mode switch itself is firmware-internal — those F-keys are spurious notifications — so disable just those three scancodes on that one device:
```sh
sudo cp keyboard/62-amira-kbd-fkeys.hwdb /etc/udev/hwdb.d/
sudo systemd-hwdb update && sudo udevadm trigger -s input --action=change
```
Verify with `sudo evtest /dev/input/eventN` (the AMIRA keyboard) — toggling should no longer emit F13/F14/F17. The mouse↔keypad switch keeps working.
