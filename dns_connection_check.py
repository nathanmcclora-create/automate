"""Check DNS connectivity for devices listed in network_devices.csv."""

import csv
import re
import subprocess
from pathlib import Path

import paramiko


CSV_FILE = Path(__file__).with_name("network_devices.csv")
DNS1 = "10.10.10.10"
DNS2 = "10.10.10.20"
USERNAME = "ubuntu"
PASSWORD = "ubuntu"
SSH_TIMEOUT_SECONDS = 10


def load_devices() -> list[dict[str, str]]:
    """Load eligible devices from the inventory CSV."""
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


def get_dns_servers(device: dict[str, str]) -> list[str]:
    """Read configured DNS servers from /etc/resolv.conf."""
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
        return re.findall(r"^\s*nameserver\s+(\S+)", output, re.MULTILINE)
    except Exception:
        return []
    finally:
        client.close()


def dns_is_reachable(server_ip: str) -> bool:
    """Ping a DNS server once to see if it responds."""
    result = subprocess.run(
        ["ping", "-c", "1", "-W", "1", server_ip],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def main() -> None:
    """Check every device and print those with broken DNS information."""
    print("Checking DNS connection for devices in network_devices.csv...\n")
    bad_devices = []

    for device in load_devices():
        dns_servers = get_dns_servers(device)
        if not dns_servers:
            bad_devices.append({"name": device["name"], "dns": "None", "status": "OFFLINE"})
            continue

        reachable = all(dns_is_reachable(server) for server in dns_servers)
        if not reachable or set(dns_servers) != {DNS1, DNS2}:
            bad_devices.append({
                "name": device["name"],
                "dns": ", ".join(dns_servers) if dns_servers else "None",
                "status": "MISCONFIGURED" if set(dns_servers) != {DNS1, DNS2} else "OFFLINE",
            })

    if not bad_devices:
        print("No devices are currently misconfigured or offline.")
        return

    print("Devices with DNS connection issues:")
    for entry in bad_devices:
        print(f"Device name: {entry['name']}")
        print(f"IP address of DNS: {entry['dns']}")
        print(f"Status: {entry['status']}")
        print()


if __name__ == "__main__":
    main()
