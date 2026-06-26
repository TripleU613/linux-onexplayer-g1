# linux-onexplayer-g1

Linux fixes for the OneXPlayer G1 A (Ryzen AI 9 HX 370), tested on Ubuntu 26.04.

## 1. Auto-rotate stuck flipping to portrait
The `bmi260` accelerometer is mounted 180° vs the panel, so `iio-sensor-proxy`
reads normal landscape as `bottom-up`. Fix = accelerometer mount-matrix quirk:

```sh
sudo cp autorotate/61-sensor-local.hwdb /etc/udev/hwdb.d/
sudo systemd-hwdb update
sudo udevadm trigger -p DEVNAME=/dev/iio:device0
sudo systemctl restart iio-sensor-proxy
```

## 2. FocalTech FT9366 fingerprint (USB 2808:c652) unsupported
No vendor ships a Linux driver. The community FT9366 shim driver already lists
`c652` in its id-table — install it, then add the udev rule and enroll:

```sh
# driver + libgusb shim:  https://github.com/leopalladium/focaltech-ft9366-arch-shim
sudo cp fingerprint/80-focaltech-c652.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
sudo systemctl restart fprintd
fprintd-enroll          # FT9366 is sleepy: firm press-and-hold, ~6-8 presses
```

Pin `libfprint-2-2` (`sudo apt-mark hold libfprint-2-2`) so updates don't overwrite the driver.
