# Creating a script to send email alerts to stakeholders when certain network devices are found to be offline or misconfigured based on the output of a DNS validation script.
# This script also retrieves SMTP server information from a CSV file or environment variables to send the email notifications.
# Emails are sent to a predefined stakeholder email address with details about the affected device(s) and the time of the check.

import csv
import os
import re
import smtplib
import subprocess
import sys
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path


CSV_FILE = Path(__file__).with_name("network_devices_2.csv")
FROM_ADDR = "network-monitoring@localdomain"
TO_ADDR = "stakeholders@localdomain"


def get_smtp_server():
    """Find the SMTP server record in the network devices CSV."""
    override_host = os.getenv("SMTP_HOST")
    override_port = os.getenv("SMTP_PORT")
    override_user = os.getenv("SMTP_USERNAME")
    override_password = os.getenv("SMTP_PASSWORD")

    if override_host:
        return {
            "host": override_host,
            "port": int(override_port or 25),
            "username": override_user or "",
            "password": override_password or "",
        }

    with CSV_FILE.open(newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            device_name = (row.get("Device Name") or "").strip().lower()
            address = (row.get("Device Address") or "").strip()
            if device_name == "smtp" and address == "10.10.10.100":
                return {
                    "host": address,
                    "port": int((row.get("Access Port") or "587").strip()),
                    "username": (row.get("Username") or "").strip(),
                    "password": (row.get("Password") or "").strip(),
                }
    raise RuntimeError("SMTP server information not found in network_devices_2.csv")


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


def parse_devices(output: str):
    """Extract device name and IP from the DNS script output."""
    pattern = re.compile(
        r"^(?P<device>.+?) \((?P<ip>\d+\.\d+\.\d+\.\d+)\) - (?P<status>OFFLINE|MISCONFIGURED)",
        re.MULTILINE,
    )

    devices = []
    for match in pattern.finditer(output):
        devices.append(
            {
                "device_name": match.group("device").strip(),
                "ip_address": match.group("ip").strip(),
                "status": match.group("status").strip(),
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
        "Network Monitoring System."
    )


def send_email(device_name: str, ip_address: str, smtp_config: dict):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body = build_email_body(device_name, ip_address, timestamp)

    message = EmailMessage()
    message["Subject"] = "Network Monitoring Alert - Device Offline"
    message["From"] = FROM_ADDR
    message["To"] = TO_ADDR
    message.set_content(body)

    try:
        with smtplib.SMTP(smtp_config["host"], smtp_config["port"], timeout=10) as server:
            server.ehlo()
            if server.has_extn("STARTTLS"):
                server.starttls()
                server.ehlo()

            username = smtp_config.get("username", "")
            password = smtp_config.get("password", "")
            if username and password and server.has_extn("AUTH"):
                server.login(username, password)

            server.send_message(message)

        print(f"Email sent for {device_name} ({ip_address}) to {smtp_config['host']}:{smtp_config['port']}")
    except Exception as exc:
        print(f"Could not send email for {device_name} ({ip_address}): {exc}")
        raise


if __name__ == "__main__":
    smtp_config = get_smtp_server()
    output = run_dns_check()
    devices = parse_devices(output)

    if not devices:
        print("No devices requiring email alerts were found in the DNS check output.")
        raise SystemExit(0)

    for device in devices:
        send_email(device["device_name"], device["ip_address"], smtp_config)
