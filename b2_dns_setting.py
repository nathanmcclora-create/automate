# Creating a script to check DNS settings on network devices listed in a CSV file, excluding certain device types based on their names.


import csv
import re
from pathlib import Path

import paramiko


CSV_FILE = Path(__file__).with_name("network_devices_2.csv")
INTERNAL_DNS_SERVERS = {"10.10.10.10", "10.10.10.20"}


def should_exclude(device_name: str) -> bool:
    name = (device_name or "").strip().lower()
    return (
        name.startswith("router")
        or name.startswith("sw")
        or "switch" in name
        or name == "smtp"
    )


def read_devices():
    """Read the CSV and return the valid devices to inspect."""
    devices = []
    with CSV_FILE.open(newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            device_name = (row.get("Device Name") or "").strip()
            if should_exclude(device_name):
                continue

            address = (row.get("Device Address") or "").strip()
            if not address or address.lower() in {"dhcp", "none"}:
                continue

            devices.append(
                {
                    "name": device_name,
                    "address": address,
                    "username": (row.get("Username") or "").strip(),
                    "password": (row.get("Password") or "").strip(),
                }
            )
    return devices


def get_dns_nameservers(command_output: str):
    """Extract nameserver entries from resolv.conf/systemd output."""
    servers = re.findall(r"^\s*nameserver\s+(\S+)", command_output, flags=re.MULTILINE)
    return servers


def check_dns_on_device(device):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=device["address"],
            username=device["username"],
            password=device["password"],
            timeout=10,
        )

        stdin, stdout, stderr = client.exec_command(
            "cat /etc/resolv.conf 2>/dev/null || resolvectl status 2>/dev/null || systemd-resolve --status 2>/dev/null"
        )
        output = stdout.read().decode("utf-8", errors="replace")
        error = stderr.read().decode("utf-8", errors="replace")

        nameservers = get_dns_nameservers(output)
        if not nameservers:
            return False, output or error or "No nameserver entries found.", []

        bad_dns = [server for server in nameservers if server not in INTERNAL_DNS_SERVERS]
        if bad_dns:
            return False, output, bad_dns
        return True, output, nameservers

    except Exception as exc:
        return False, str(exc), []

    finally:
        client.close()


if __name__ == "__main__":
    devices = read_devices()
    print(f"Checking DNS on {len(devices)} devices...\n")

    for device in devices:
        name = device["name"]
        address = device["address"]
        status, details, dns_servers = check_dns_on_device(device)

        if status:
            print(f"{name} ({address}) - OK")
            print(f"  DNS: {dns_servers}")
        else:
            print(f"{name} ({address}) - MISCONFIGURED")
            print(f"  DNS servers found: {dns_servers if dns_servers else 'None'}")
            print(f"  Raw config:\n{details[:500]}")
