import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


OUTPUT_FILE = Path(__file__).with_name("dns_misconfiguration_emails.txt")


def get_misconfigured_devices():
    """Run b2_dns_setting.py and extract each misconfigured device from its console output."""
    try:
        result = subprocess.run(
            [sys.executable, "b2_dns_setting.py"],
            capture_output=True,
            text=True,
            check=False,
            cwd=str(Path(__file__).resolve().parent),
        )
    except FileNotFoundError:
        print("Could not find b2_dns_setting.py")
        return []

    output = result.stdout + result.stderr
    pattern = re.compile(r"^(?P<device>.+?) \((?P<ip>\d+\.\d+\.\d+\.\d+)\) - MISCONFIGURED", re.MULTILINE)

    devices = []
    for match in pattern.finditer(output):
        devices.append({
            "device_name": match.group("device").strip(),
            "ip_address": match.group("ip").strip(),
        })

    return devices


def build_email(device_name: str, ip_address: str, timestamp: str) -> str:
    return f"""Dear Stakeholders,

This is an automated alert to inform you that the following device(s) have been identified as compromised during the recent network scan:

Device Name: {device_name}
IP Address: {ip_address}
Last Checked: {timestamp}

Immediate investigation and remediation are recommended to prevent further impact.

If you have any questions or require additional information, please contact the IT support team.

Best regards,  
Network Monitoring System
"""


def save_emails(emails):
    OUTPUT_FILE.write_text("\n\n---\n\n".join(emails), encoding="utf-8")
    print(f"Saved {len(emails)} email message(s) to {OUTPUT_FILE}")


if __name__ == "__main__":
    misconfigured = get_misconfigured_devices()

    if not misconfigured:
        print("No misconfigured devices were found in the output from b2_dns_setting.py.")
        raise SystemExit(0)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    email_messages = [
        build_email(device["device_name"], device["ip_address"], timestamp)
        for device in misconfigured
    ]

    for message in email_messages:
        print(message)
        print("\n" + "-" * 60 + "\n")

    save_emails(email_messages)
