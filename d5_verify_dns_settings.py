"""Verify DNS settings on eligible devices in network_devices.csv."""

import csv
import re
import socket
import time
from pathlib import Path

import paramiko


CSV_FILE = Path(__file__).with_name("network_devices.csv")
APPROVED_DNS_SERVERS = {"10.10.10.10", "10.10.10.20"}
SSH_TIMEOUT_SECONDS = 10
CONSOLE_TIMEOUT_SECONDS = 5


def should_check(name: str, address: str) -> bool:
    """Exclude infrastructure and entries without an address or DHCP marker."""
    device_name = name.strip().lower()
    device_address = address.strip().lower()
    return (
        bool(device_address)
        and device_address != "none"
        and not device_name.startswith("router")
        and not device_name.startswith("sw")
        and "switch" not in device_name
        and device_name != "smtp"
    )


def load_devices() -> list[dict[str, str]]:
    """Load eligible device information, credentials, and console ports."""
    with CSV_FILE.open(newline="", encoding="utf-8") as csv_file:
        devices = []
        for row in csv.DictReader(csv_file):
            name = (row.get("Device Name") or "").strip()
            address = (row.get("Device Address") or "").strip()
            if should_check(name, address):
                devices.append(
                    {
                        "name": name,
                        "address": address,
                        "access_port": (row.get("Access Port") or "").strip(),
                        "username": (row.get("Username") or "ubuntu").strip(),
                        "password": (row.get("Password") or "ubuntu").strip(),
                    }
                )
        return devices


def run_console_command(device: dict[str, str], command: str) -> tuple[str, str]:
    """Run a command on a DHCP device through its local GNS3 console."""
    try:
        with socket.create_connection(
            ("127.0.0.1", int(device["access_port"])),
            timeout=CONSOLE_TIMEOUT_SECONDS,
        ) as console:
            console.settimeout(0.5)
            output = b""
            try:
                while True:
                    output += console.recv(4096)
            except (socket.timeout, ConnectionResetError):
                pass

            console.sendall(f"{device['username']}\n".encode())
            time.sleep(0.2)
            console.sendall(f"{device['password']}\n".encode())
            time.sleep(0.5)
            console.sendall(f"{command}\n".encode())
            time.sleep(0.5)
            while True:
                try:
                    output += console.recv(4096)
                except socket.timeout:
                    break
            return output.decode("utf-8", errors="replace"), ""
    except (OSError, ValueError) as exc:
        return "", str(exc)


def read_dhcp_dns(device: dict[str, str]) -> tuple[list[str], str]:
    """Read DNS nameservers from a DHCP device using its CSV credentials."""
    output, error = run_console_command(
        device, "cat /etc/resolv.conf 2>/dev/null || resolvectl dns"
    )
    servers = re.findall(r"^\s*nameserver\s+(\S+)", output, re.MULTILINE)
    return servers, error


def read_ssh_dns(device: dict[str, str]) -> tuple[list[str], str]:
    """Read DNS nameservers from a fixed-address device over SSH."""
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
        _, stdout, stderr = client.exec_command(
            "cat /etc/resolv.conf 2>/dev/null || resolvectl dns",
            timeout=SSH_TIMEOUT_SECONDS,
        )
        output = stdout.read().decode("utf-8", errors="replace")
        error = stderr.read().decode("utf-8", errors="replace").strip()
        servers = re.findall(r"^\s*nameserver\s+(\S+)", output, re.MULTILINE)
        return servers, error
    except Exception as exc:
        return [], str(exc)
    finally:
        client.close()


def verify_device(device: dict[str, str]) -> bool:
    """Print current and expected DNS settings for one device."""
    address_label = "DHCP" if device["address"].lower() == "dhcp" else device["address"]
    if device["address"].lower() == "dhcp":
        servers, error = read_dhcp_dns(device)
    else:
        servers, error = read_ssh_dns(device)

    correct = set(servers) == APPROVED_DNS_SERVERS
    status = "PASS" if correct else "FAIL"
    print(f"{device['name']} ({address_label}) - {status}")
    print(f"  Current DNS: {servers or 'None'}")
    print(f"  Expected DNS: {sorted(APPROVED_DNS_SERVERS)}")
    if error:
        print(f"  Connection error: {error}")
    return correct


def main() -> int:
    """Verify every eligible device in the inventory."""
    devices = load_devices()
    print(f"Verifying DNS settings on {len(devices)} devices...\n")
    results = [verify_device(device) for device in devices]
    passed = sum(results)
    print(f"\nVerification complete: {passed}/{len(results)} devices passed.")
    return 0 if results and all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
