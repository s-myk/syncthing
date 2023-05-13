#!/usr/bin/env python3

import json
import os
from pathlib import Path
import subprocess
from subprocess import PIPE
from urllib import request
import xml.etree.ElementTree as ET

SYNCTHING_ENDPOINT = "http://localhost:8384/rest/stats/device"
SYNCTHING_CONFIG = Path.home().joinpath(".config/syncthing/config.xml")
SYNCTHING_OBSOLETE_DEVICES = \
    Path(__file__).parent.joinpath("syncthing_obsolete_devices.txt")
# Synology NAS
# SYNCTHING_CONFIG = Path("/volume1/@appdata/syncthing/config.xml")


def find_duplicate_device_ids(root: ET.Element) -> dict[str, list[str]]:
    syncthing_device: dict[str, list[str]] = {}
    for device in root.findall("device"):
        name: str = device.get("name") or ""
        device_id: str = device.get("id") or ""

        syncthing_device.get(name, []).append(device_id)

    for name in list(syncthing_device.keys()):
        if len(syncthing_device[name]) < 2:
            syncthing_device.pop(name)

    return syncthing_device


def find_obsolete_device_ids(root: ET.Element) -> list[str]:
    guikey = root.find("gui/apikey")
    if guikey is not None and guikey.text is not None:
        apikey = guikey.text
    else:
        apikey = ""

    last_seen: dict[str, str] = {}

    req = request.Request(SYNCTHING_ENDPOINT)
    req.headers = {"X-API-Key": os.getenv("SYNCTHING_APIKEY", apikey)}

    try:
        with request.urlopen(req) as res:
            syncthing_stats = json.loads(res.read().decode('utf-8'))
        for device_id in syncthing_stats.keys():
            last_seen[device_id] = syncthing_stats[device_id]["lastSeen"]

    except Exception:
        with open(SYNCTHING_OBSOLETE_DEVICES) as f:
            return [line.split()[0] for line in f.readlines()]

    with open(SYNCTHING_OBSOLETE_DEVICES) as f:
        obsolete_devices: list[str] = [line for line in f.readlines() if len(line) >= 8]

    duplicate: dict[str, list[str]] = find_duplicate_device_ids(root)

    for name in duplicate.keys():
        lastSeen: str = "1970-01-01T09:00:00+09:00"
        for device_id in duplicate[name]:
            if lastSeen < last_seen[device_id]:
                lastSeen = last_seen[device_id]
            else:
                obsolete_devices.append(f"{device_id}\t{name}\n")

    with open(SYNCTHING_OBSOLETE_DEVICES, "w") as f:
        f.writelines(set(obsolete_devices))
        # filter(None, obsolete_devices)

    return [line.split()[0] for line in set(obsolete_devices)]


def remove_obsolete_device(root: ET.Element, device_id: str) -> None:
    obsolete_device = root.find(f"device[@id='{device_id}']")
    if obsolete_device is not None:
        root.remove(obsolete_device)

    for folder in root.findall("folder"):
        device = folder.find(f"device[@id='{device_id}']")
        if device is not None:
            folder.remove(device)


def add_tailscale_address(root: ET.Element) -> None:
    tailscale: dict[str, str] = {}
    proc = subprocess.run(
        "tailscale status",
        shell=True, stdout=PIPE, stderr=PIPE, text=True
    )
    for line in filter(None, proc.stdout.split("\n")):
        ip, name = line.split()[0:2]
        tailscale[name] = ip

    for device in root.findall("device"):
        name = (device.get("name") or "").lower()
        if name in tailscale:
            for address in device.findall("address"):
                device.remove(address)

            ip4 = ET.SubElement(device, "address")
            ip4.text = f"tcp4://{tailscale[name]}"

            ts = ET.SubElement(device, "address")
            ts.text = f"tcp4://{name}"

            dynamic = ET.SubElement(device, "address")
            dynamic.text = "dynamic"


def main():
    if not SYNCTHING_OBSOLETE_DEVICES.exists():
        with open(SYNCTHING_OBSOLETE_DEVICES, "w"):
            pass

    tree = ET.parse(SYNCTHING_CONFIG)
    root = tree.getroot()

    obsolete_device_ids: list[str] = find_obsolete_device_ids(root)

    for device_id in obsolete_device_ids:
        print(device_id)
        remove_obsolete_device(root, device_id)

    add_tailscale_address(root)

    tree.write(SYNCTHING_CONFIG)
    tree.write(Path(__file__).parent.joinpath("syncthing_config.xml"))


if __name__ == "__main__":
    main()
