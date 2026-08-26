"""Verify that each managed device uses the internal DNS servers."""

import csv
import re
import sys
from pathlib import Path

import paramiko


CSV_FILE = Path(__file__).with_name("network_devices_2.csv")
APPROVED_DNS_SERVERS = {"10.10.10.10", "10.10.10.20"}
USERNAME = "ubuntu"
PASSWORD = "ubuntu"
SSH_TIMEOUT_SECONDS = 10


def should_check(device_name: str, address: str) -> bool:
    """Return whether a CSV device is an SSH-managed host to verify."""
    name = device_name.strip().lower()
    return (
        bool(address)
        and address.lower() not in {"dhcp", "none"}
        and not name.startswith("router")
        and not name.startswith("sw")
        and "switch" not in name
        and name != "smtp"
    )


def load_devices() -> list[dict[str, str]]:
    """Load valid device names and addresses from the inventory CSV."""
    with CSV_FILE.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        return [
            {"name": row.get("Device Name", "").strip(), "address": row.get("Device Address", "").strip()}
            for row in reader
            if should_check(row.get("Device Name", ""), row.get("Device Address", ""))
        ]


def read_dns_servers(device: dict[str, str]) -> tuple[list[str], str]:
    """Connect to a device and read its configured nameservers."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=device["address"],
            username=USERNAME,
            password=PASSWORD,
            timeout=SSH_TIMEOUT_SECONDS,
            banner_timeout=SSH_TIMEOUT_SECONDS,
            auth_timeout=SSH_TIMEOUT_SECONDS,
        )
        _, stdout, stderr = client.exec_command(
            "cat /etc/resolv.conf 2>/dev/null || resolvectl dns",
            timeout=SSH_TIMEOUT_SECONDS,
        )
        output = stdout.read().decode("utf-8", errors="replace")
        error = stderr.read().decode("utf-8", errors="replace").strip()
        servers = re.findall(r"^\s*nameserver\s+(\S+)", output, re.MULTILINE)
        return servers, error
    finally:
        client.close()


def verify_device(device: dict[str, str]) -> bool:
    """Print one device's DNS settings and return whether they are correct."""
    print(f"\n{device['name']} ({device['address']})")
    try:
        servers, error = read_dns_servers(device)
        correct = set(servers) == APPROVED_DNS_SERVERS
        status = "SUCCESS - DNS settings changed correctly" if correct else "FAILED - DNS settings are incorrect"
        print(f"  Configured DNS: {servers or 'None'}")
        print(f"  Expected DNS: {sorted(APPROVED_DNS_SERVERS)}")
        print(f"  {status}")
        if error:
            print(f"  Command errors: {error}")
        return correct
    except Exception as exc:
        print(f"  FAILED - unable to verify device: {exc}")
        return False


def main() -> int:
    devices = load_devices()
    print(f"Verifying DNS settings on {len(devices)} devices...")
    results = [verify_device(device) for device in devices]
    successful = sum(results)
    print(f"\nVerification complete: {successful}/{len(devices)} devices have the correct DNS settings.")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
