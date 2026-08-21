import re
import smtplib
import subprocess
import sys
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path


SMTP_HOST = "localhost"
SMTP_PORT = 1025
FROM_ADDR = "network-monitoring@localdomain"
TO_ADDR = "stakeholders@localdomain"


def run_dns_check():
    """Run the DNS validation script and return its combined output."""
    result = subprocess.run(
        [sys.executable, "b2_dns_setting.py"],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(Path(__file__).resolve().parent),
    )
    return result.stdout + result.stderr


def parse_misconfigured_devices(output: str):
    """Extract device name and IP from the DNS script output."""
    pattern = re.compile(
        r"^(?P<device>.+?) \((?P<ip>\d+\.\d+\.\d+\.\d+)\) - MISCONFIGURED",
        re.MULTILINE,
    )

    devices = []
    for match in pattern.finditer(output):
        devices.append(
            {
                "device_name": match.group("device").strip(),
                "ip_address": match.group("ip").strip(),
            }
        )
    return devices


def build_email_body(device_name: str, ip_address: str, timestamp: str) -> str:
    return (
        "Dear Stakeholders,\n\n"
        "This is an automated alert to inform you that the following device(s) have been identified as compromised during the recent network scan:\n\n"
        f"Device Name: {device_name}\n"
        f"IP Address: {ip_address}\n"
        f"Last Checked: {timestamp}\n\n"
        "Immediate investigation and remediation are recommended to prevent further impact.\n\n"
        "If you have any questions or require additional information, please contact the IT support team.\n\n"
        "Best regards,\n"
        "Network Monitoring System\n"
    )


def send_email(device_name: str, ip_address: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body = build_email_body(device_name, ip_address, timestamp)

    message = EmailMessage()
    message["Subject"] = "Network Monitoring Alert - Misconfigured DNS Device"
    message["From"] = FROM_ADDR
    message["To"] = TO_ADDR
    message.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.send_message(message)
        print(f"Email sent for {device_name} ({ip_address}) to MailHog at {SMTP_HOST}:{SMTP_PORT}")
    except OSError as exc:
        print(f"Could not connect to MailHog SMTP at {SMTP_HOST}:{SMTP_PORT}: {exc}")
        print("Start MailHog with the SMTP port enabled, then rerun this script.")
        raise SystemExit(1)


if __name__ == "__main__":
    output = run_dns_check()
    misconfigured_devices = parse_misconfigured_devices(output)

    if not misconfigured_devices:
        print("No misconfigured devices were found in the output from b2_dns_setting.py.")
        raise SystemExit(0)

    for device in misconfigured_devices:
        send_email(device["device_name"], device["ip_address"])
