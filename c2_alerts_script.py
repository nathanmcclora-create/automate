"""Create Helpdesk API tickets for DNS alerts and print the API responses."""

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_HOST = "api.d522.wgu.internal"
API_PORT = 5000
TICKETS_PATH = "/api/tickets"
API_TOKEN = "vGkbXkGLqQSo7YLflp9DutuG8st4xdPPF7wnTcwB0FE"
API_URL = f"http://{API_HOST}:{API_PORT}{TICKETS_PATH}"
DNS_CHECK_SCRIPT = Path(__file__).with_name("b2_dns_setting.py")


def api_request(method: str, payload: dict | None = None) -> tuple[int, object]:
	"""Send an authenticated request and return its HTTP status and JSON body."""
	body = None if payload is None else json.dumps(payload).encode("utf-8")
	request = Request(
		API_URL,
		data=body,
		method=method,
		headers={
			"Authorization": f"Bearer {API_TOKEN}",
			"Accept": "application/json",
			"Content-Type": "application/json",
		},
	)

	try:
		with urlopen(request, timeout=15) as response:
			response_body = response.read().decode("utf-8")
			return response.status, json.loads(response_body) if response_body else {}
	except HTTPError as exc:
		error_body = exc.read().decode("utf-8", errors="replace")
		try:
			details = json.loads(error_body)
		except json.JSONDecodeError:
			details = error_body
		return exc.code, details
	except URLError as exc:
		raise RuntimeError(f"Could not connect to {API_URL}: {exc.reason}") from exc


def verify_api_access() -> None:
	"""Verify authentication and ticket creation with a harmless test ticket."""
	status, response = api_request(
		"POST",
		{
			"title": "Helpdesk API connectivity test",
			"description": "Test ticket created by c2_alerts_script.py to verify Helpdesk API access.",
			"priority": "medium",
		},
	)
	print(f"API connectivity test: HTTP {status}")
	print(json.dumps(response, indent=2))
	if not 200 <= status < 300 or not isinstance(response, dict) or "id" not in response:
		raise RuntimeError("Helpdesk API connectivity test was not successful.")


def run_dns_check() -> str:
	"""Run the DNS validation script and return its combined output."""
	result = subprocess.run(
		[sys.executable, str(DNS_CHECK_SCRIPT)],
		capture_output=True,
		text=True,
		check=False,
		cwd=str(DNS_CHECK_SCRIPT.parent),
	)
	return result.stdout + result.stderr


def parse_alert_devices(output: str) -> list[dict[str, str]]:
	"""Extract device details from MISCONFIGURED DNS check results."""
	pattern = re.compile(
		r"^(?P<device>.+?) \((?P<ip>[^)]+)\) - (?P<status>OK|MISCONFIGURED)\s*$",
		re.MULTILINE,
	)
	devices = []
	matches = list(pattern.finditer(output))
	for index, match in enumerate(matches):
		if match.group("status") != "MISCONFIGURED":
			continue
		next_match_start = matches[index + 1].start() if index + 1 < len(matches) else len(output)
		devices.append(
			{
				"device_name": match.group("device").strip(),
				"ip_address": match.group("ip").strip(),
				"details": output[match.end() : next_match_start].strip(),
			}
		)
	return devices


def create_alert_ticket(device: dict[str, str]) -> tuple[int, object]:
	"""Create one Helpdesk ticket for a device alert."""
	checked_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
	payload = {
		"title": f"DNS configuration alert: {device['device_name']} ({device['ip_address']})",
		"description": (
			"The device is misconfigured or could not be checked for the required DNS servers.\n\n"
			f"Device: {device['device_name']}\n"
			f"Address: {device['ip_address']}\n"
			f"Checked at: {checked_at}\n"
			f"Details: {device['details']}"
		),
		"priority": "medium",
	}
	return api_request("POST", payload)


def main() -> int:
	try:
		verify_api_access()
		devices = parse_alert_devices(run_dns_check())
		if not devices:
			print("No misconfigured devices were found; no alert tickets were created.")
			return 0

		all_successful = True
		for device in devices:
			status, response = create_alert_ticket(device)
			successful = 200 <= status < 300 and isinstance(response, dict) and "id" in response
			all_successful = all_successful and successful
			result = "SUCCESS" if successful else "FAILED"
			print(f"\n{result}: {device['device_name']} ({device['ip_address']}) - HTTP {status}")
			print(json.dumps(response, indent=2))
		return 0 if all_successful else 1
	except (RuntimeError, OSError) as exc:
		print(f"ERROR: {exc}", file=sys.stderr)
		return 1


if __name__ == "__main__":
	raise SystemExit(main())
