#!/bin/bash
# GDM greeter launched a full 'ubuntu' desktop (gnome-shell --mode=ubuntu) instead
# of the login screen -> no user list, just a "GDM Greeter" lock screen.
# Cause: /etc/dconf/profile/gdm was missing the file-db line, so the upstream
# session-name=gnome-login (in /var/lib/gdm3/greeter-dconf-defaults) never loaded,
# and the per-seat state had a saved 'ubuntu' session pinning it. Reinstalling gdm3
# does NOT fix it (the profile is generated at runtime, not shipped by the package).
set -e

# 1. restore the greeter dconf profile (the missing file-db line is the bug)
printf 'user-db:user\nsystem-db:gdm\nfile-db:/var/lib/gdm3/greeter-dconf-defaults\n' \
  | sudo tee /etc/dconf/profile/gdm >/dev/null

# 2. force + lock the greeter session so a contaminated user-db can't override it
sudo install -d /etc/dconf/db/gdm.d/locks
printf "[org/gnome/desktop/session]\nsession-name='gnome-login'\n" \
  | sudo tee /etc/dconf/db/gdm.d/01-greeter-session >/dev/null
printf '/org/gnome/desktop/session/session-name\n' \
  | sudo tee /etc/dconf/db/gdm.d/locks/01-greeter-session >/dev/null
sudo dconf update

# 3. wipe the contaminated per-seat state (the saved 'ubuntu' session) and restart
sudo rm -rf /var/lib/gdm3/seat0
sudo systemctl restart gdm

# verify: greeter now runs `gnome-shell --mode=gdm` and lists your user:
#   ps -u $(id -u Debian-gdm 2>/dev/null || echo gdm) -o args | grep gnome-shell
