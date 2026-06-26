#!/bin/sh
# OneXPlayer G1 A fixes for an installed Howdy (/lib/security/howdy).
# Prereq: Howdy installed, and dlib built for your Python (e.g. `pip wheel dlib`).
set -e
H=/lib/security/howdy

# 1. pam.py ships Python-2 code -> won't load under Python 3 -> silent password fallback
sudo sed -i 's/^import ConfigParser$/import configparser as ConfigParser/' "$H/pam.py"

# 2. Point at the IR camera via a STABLE path (verify it resolves to the GREY node!)
sudo sed -i 's#^device_path = .*#device_path = /dev/v4l/by-path/pci-0000:c7:00.0-usb-0:4:1.2-video-index0#' "$H/config.ini"

# 3. OpenCV must use V4L2 (GStreamer can't open the cam) + rotate IR frames 90° CW (mounted rotated)
sudo python3 - "$H/recorders/video_capture.py" <<'PY'
import sys; p=sys.argv[1]; s=open(p).read()
s=s.replace('self.config.get("video", "device_path")\n\t\t\t)',
            'self.config.get("video", "device_path"), cv2.CAP_V4L2\n\t\t\t)')
a='gsframe = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)'
if 'ROTATE_90_CLOCKWISE' not in s:
    s=s.replace(a,'frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)\n\t\t\t'+a,1)
open(p,'w').write(s)
PY
echo "Howdy patched. Now: sudo howdy -U \$USER add  &&  sudo pam-auth-update --enable howdy"
