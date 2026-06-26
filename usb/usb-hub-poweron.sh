#!/bin/bash
udevadm settle --timeout=60
for d in /sys/bus/usb/devices/*/power/control; do
    echo on > "$d" 2>/dev/null
done
