"""Set the internal DNS servers on each device listed in network_devices.csv."""

import csv
import shlex
from pathlib import Path

import paramiko


CSV_FILE = Path(__file__).with_name("network_devices.csv")
DNS1 = "10.10.10.10"
DNS2 = "10.10.10.20"
USERNAME = "ubuntu"
PASSWORD = "ubuntu"
SSH_TIMEOUT_SECONDS = 10


def load_devices() -> list[dict[str, str]]:
    """Load eligible devices from the CSV."""
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


def set_dns(server: dict[str, str]) -> bool:
    """Replace the device's DNS servers with the correct internal servers."""
    command = (
        f"printf '%s\\n' 'nameserver {DNS1}' 'nameserver {DNS2}' "
        "'options timeout:2 attempts:2' > /etc/resolv.conf"
    )
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=server["address"],
            username=server["username"],
            password=server["password"],
            timeout=SSH_TIMEOUT_SECONDS,
            banner_timeout=SSH_TIMEOUT_SECONDS,
            auth_timeout=SSH_TIMEOUT_SECONDS,
        )
        stdin, stdout, stderr = client.exec_command(
            f"sudo -S -p '' sh -c {shlex.quote(command)}",
            get_pty=True,
            timeout=SSH_TIMEOUT_SECONDS,
        )
        stdin.write(f"{server['password']}\n")
        stdin.flush()
        stdout_text = stdout.read().decode("utf-8", errors="replace")
        stderr_text = stderr.read().decode("utf-8", errors="replace")
        result = stdout.channel.recv_exit_status() == 0
        if stdout_text:
            print(stdout_text.strip())
        if stderr_text:
            print(stderr_text.strip())
        return result
    except Exception as exc:
        print(f"Failed to update DNS on {server['name']}: {exc}")
        return False
    finally:
        client.close()


def main() -> None:
    """Fix the DNS configuration for each device."""
    print("Updating incorrect DNS settings to the internal DNS servers...\n")
    for device in load_devices():
        print(f"Device: {device['name']} ({device['address']})")
        success = set_dns(device)
        if success:
            print(f"Status: SUCCESS - {device['name']} now points to DNS1 ({DNS1}) and DNS2 ({DNS2})")
        else:
            print(f"Status: FAILED - {device['name']} could not be updated")
        print()


if __name__ == "__main__":
    main()
