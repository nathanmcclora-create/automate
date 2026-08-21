# Creating a script to ping network devices listed in a CSV file, excluding certain device types based on their names.

import csv
import subprocess
from pathlib import Path


CSV_FILE = Path(__file__).with_name("network_devices_2.csv")


def should_exclude(device_name: str) -> bool:
    name = (device_name or "").strip().lower()
    return (
        name.startswith("router")
        or name.startswith("sw")
        or "switch" in name
        or name == "smtp"
    )


def get_ping_targets():
    with CSV_FILE.open(newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        targets = []
        for row in reader:
            device_name = row.get("Device Name", "")
            if should_exclude(device_name):
                continue

            address = (row.get("Device Address") or "").strip()
            if not address or address.lower() in {"dhcp", "none"}:
                continue

            targets.append((device_name, address))
    return targets


def ping_host(ip_address: str) -> bool:
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip_address],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        print("ping command not available on this system.")
        return False


if __name__ == "__main__":
    for name, address in get_ping_targets():
        print(f"Pinging {name} ({address})...")
        if ping_host(address):
            print(f"SUCCESS: {name} reachable at {address}")
        else:
            print(f"FAILED: {name} unreachable at {address}")
