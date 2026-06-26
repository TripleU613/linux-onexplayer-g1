#!/usr/bin/env python3
# Direct RGB control for OneXPlayer G1 A controller LEDs.
# HHD detects the device but never actually writes RGB (its pipeline is broken
# for the G1 A: logs "Setting RGB" but no device write). This writes the OXP
# vendor command straight to the hidraw device. Command format reverse-engineered
# from hhd/device/oxp/hid_v1.py.
import os, sys, glob, time, configparser

CONF = "/etc/oxp-rgb.conf"
VID, PID = "1A2C", "B001"          # OXP vendor hidraw
EFFECTS = {"aurora":0x01,"flowing":0x03,"neon":0x05,"dreamy":0x07,"sun":0x08,
           "cyberpunk":0x09,"sunset":0x0B,"colorful":0x0C,"monster_woke":0x0D}
BRIGHT = {"low":0x01,"medium":0x03,"high":0x04}

def gen_cmd(cid, cmd, idx=0x01, size=64):
    base = bytes([cid, 0x3F, idx]) + bytes(cmd)
    return base + bytes([0]*(size-len(base)-2)) + bytes([0x3F, cid])
def gen_brightness(side, en, bc): return gen_cmd(0xB8, [0xFD, side, 0x02, 1 if en else 0, 0x05, bc])
def gen_rgb_solid(r,g,b, side=0): return gen_cmd(0xB8, [0xFE, side, 0x02] + 18*[r,g,b] + [r,g])
def gen_rgb_mode(mc): return gen_cmd(0xB8, [mc, 0x00, 0x02])

def find_dev():
    for hr in sorted(glob.glob("/sys/class/hidraw/hidraw*")):
        try:
            u = open(os.path.join(hr, "device/uevent")).read().upper()
        except OSError:
            continue
        if VID in u and PID in u:
            return "/dev/" + os.path.basename(hr)
    return None

def main():
    c = configparser.ConfigParser()
    c.read(CONF)
    g = c["rgb"] if c.has_section("rgb") else {}
    mode = g.get("mode", "effect")
    bc = BRIGHT.get(g.get("brightness", "high"), 0x04)
    dev = find_dev()
    if not dev:
        print("OXP RGB device not found", file=sys.stderr); sys.exit(1)
    fd = os.open(dev, os.O_RDWR)
    def w(cmd): os.write(fd, bytes(cmd)); time.sleep(0.08)
    w(gen_brightness(0, True, bc))
    if mode == "solid":
        r,gn,b = int(g.get("r",0)), int(g.get("g",255)), int(g.get("b",0))
        for side in (0x00, 0x01, 0x02):
            w(gen_rgb_solid(r, gn, b, side=side))
        print(f"set solid {r},{gn},{b} on {dev}")
    else:
        eff = g.get("effect", "aurora")
        w(gen_rgb_mode(EFFECTS.get(eff, 0x01)))
        print(f"set effect '{eff}' on {dev}")
    os.close(fd)

if __name__ == "__main__":
    main()
