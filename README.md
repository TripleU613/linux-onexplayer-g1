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

## 6. USB peripherals on the internal hub flap / `-71` (WIP)
The G1's internal USB (QinHeng `1a86:8091` hub) and a passive Genesys hub (`05e3:0610`) are power-marginal: hot-plugged receivers `attempt power cycle` / `error -71`. Boot-time quirks help (`usbcore.quirks=...:e` reset, `old_scheme_first`, `usbcore.autosuspend=-1`, the `usb-hub-poweron.service`). Bare low-power receivers work in a strong port; a powered hub is the reliable fix for combo (keyboard+mouse+speaker) receivers. **Open:** a 2.4 GHz receiver that works at the greeter goes dead in the session after login (greeter-vs-session device handoff) — not yet root-caused.
