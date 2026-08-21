# Creating a script to list network devices from a CSV file and print their details.

import csv
from pathlib import Path


def list_devices(csv_file: str = "network_devices_2.csv") -> None:
    """Read the CSV and print each device entry."""
    csv_path = Path(__file__).with_name(csv_file)

    with csv_path.open("r", newline="") as file:
        reader = csv.DictReader(file)

        print("Devices in CSV:")
        for row in reader:
            device_id = row.get("Device ID", "Unknown")
            device_name = row.get("Device Name", "Unknown")
            device_address = row.get("Device Address", "Unknown")
            print(f"{device_id}: {device_name} ({device_address})")


if __name__ == "__main__":
    list_devices()
