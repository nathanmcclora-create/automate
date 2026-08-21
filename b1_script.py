#!/usr/bin/env python3
from pathlib import Path
import csv

CSV_PATH = Path(__file__).with_name("network_devices_2.csv")


def load_devices(csv_path: Path):
    """Read network device data from the CSV file and return a list of dicts."""
    devices = []

    with csv_path.open("r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            clean_row = {
                key.strip(): (value.strip() if isinstance(value, str) else value)
                for key, value in row.items()
            }
            devices.append(clean_row)

    return devices


def main():
    devices = load_devices(CSV_PATH)
    print(f"Loaded {len(devices)} devices from {CSV_PATH.name}")

    for device in devices:
        name = device.get("Device Name", "Unknown")
        address = device.get("Device Address", "Unknown")
        location = device.get("Location", "Unknown")
        print(f"{name:<12} | {address:<15} | {location}")


if __name__ == "__main__":
    main()
