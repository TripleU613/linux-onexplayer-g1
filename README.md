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
