"""Verify that device DNS settings were updated to the internal DNS servers."""

import csv
import re
from pathlib import Path

import paramiko


CSV_FILE = Path(__file__).with_name("network_devices.csv")
DNS1 = "10.10.10.10"
DNS2 = "10.10.10.20"
USERNAME = "ubuntu"
PASSWORD = "ubuntu"
SSH_TIMEOUT_SECONDS = 10


def load_devices() -> list[dict[str, str]]:
    """Load all target devices from the CSV."""
    devices: list[dict[str, str]] = []
    with CSV_FILE.open(newline="", encoding="utf-8") as csv_file:
        for row in csv.DictReader(csv_file):
            name = (row.get("Device Name") or "").strip()
            address = (row.get("Device Address") or "").strip()
            if not address or address.lower() in {"dhcp", "none"}:
                continue
            lower_name = name.lower()
            if lower_name.startswith("router") or lower_name.startswith("sw") or "switch" in lower_name or lower_name == "smtp":
                continue
            devices.append(
                {
                    "name": name,
                    "address": address,
                    "username": (row.get("Username") or USERNAME).strip() or USERNAME,
                    "password": (row.get("Password") or PASSWORD).strip() or PASSWORD,
                }
            )
    return devices


def check_dns(device: dict[str, str]) -> tuple[bool, list[str]]:
    """Read the current DNS servers and compare them to the internal DNS servers."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=device["address"],
            username=device["username"],
            password=device["password"],
            timeout=SSH_TIMEOUT_SECONDS,
            banner_timeout=SSH_TIMEOUT_SECONDS,
            auth_timeout=SSH_TIMEOUT_SECONDS,
        )
        _, stdout, _ = client.exec_command(
            "cat /etc/resolv.conf 2>/dev/null || resolvectl dns",
            timeout=SSH_TIMEOUT_SECONDS,
        )
        output = stdout.read().decode("utf-8", errors="replace")
        servers = re.findall(r"^\s*nameserver\s+(\S+)", output, re.MULTILINE)
        return set(servers) == {DNS1, DNS2}, servers
    except Exception:
        return False, []
    finally:
        client.close()


def main() -> None:
    """Verify the correct DNS settings on every device."""
    print("Verifying DNS updates across devices...\n")
    for device in load_devices():
        success, servers = check_dns(device)
        if success:
            print(f"Device name: {device['name']}")
            print(f"DNS1: {DNS1}")
            print(f"DNS2: {DNS2}")
            print("Status: SUCCESS")
        else:
            print(f"Device name: {device['name']}")
            print(f"Current DNS: {servers or 'None'}")
            print("Status: FAILED")
        print()


if __name__ == "__main__":
    main()
