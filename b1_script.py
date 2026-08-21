import csv
from pathlib import Path


CSV_FILE = Path(__file__).with_name("network_devices_2.csv")


def should_exclude(device_name: str) -> bool:
    """Return True for devices that should be skipped."""
    name = device_name.strip().lower()
    return (
        name.startswith("router")
        or name.startswith("sw")
        or "switch" in name
        or name == "smtp"
    )


def load_devices():
    """Read the CSV and return only valid devices."""
    with CSV_FILE.open(newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        return [row for row in reader if not should_exclude(row["Device Name"])]


if __name__ == "__main__":
    devices = load_devices()
    print(f"Remaining devices: {len(devices)}")
    for device in devices:
        print(f"{device['Device Name']} - {device['Device Address']}")
