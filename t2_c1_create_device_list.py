#!/usr/bin/env python3

"""Print a filtered list of network devices from the CSV inventory."""

from __future__ import annotations

import csv
from pathlib import Path


def is_excluded(device_name: str) -> bool:
    """Return True when the device should be filtered out from the report."""
    normalized = (device_name or "").strip().upper()
    return "ROUTER" in normalized or "SW" in normalized or normalized == "SMTP"


def get_csv_path() -> Path:
    """Resolve the inventory CSV path, supporting both singular and plural names."""
    home_dir = Path.home()
    candidates = [
        home_dir / "d522" / "network_device.csv",
        home_dir / "d522" / "network_devices.csv",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(f"No device inventory CSV found in {home_dir / 'd522'}")


def main() -> None:
    csv_path = get_csv_path()

    print("ID,Hostname,IP Address")

    with csv_path.open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            device_name = (row.get("Device Name") or "").strip()
            if is_excluded(device_name):
                continue

            device_id = (row.get("Device ID") or "").strip()
            ip_address = (row.get("Device Address") or "").strip()
            print(f"{device_id},{device_name},{ip_address}")


if __name__ == "__main__":
    main()
