#!/bin/sh
# Screen was stuck dim: GNOME auto-brightness drives off the bmi260, which is an
# IMU (not a light sensor), so it dimmed wrongly. Turn it off.
gsettings set org.gnome.settings-daemon.plugins.power ambient-enabled false
