"""Correct compromised DNS settings and verify the resulting configuration."""

import re
import shlex
import subprocess
import sys
from pathlib import Path

import paramiko


DNS1 = "10.10.10.10"
DNS2 = "10.10.10.20"
USERNAME = "ubuntu"
PASSWORD = "ubuntu"
SSH_TIMEOUT_SECONDS = 10
DNS_CHECK_SCRIPT = Path(__file__).with_name("b2_dns_setting.py")


def run_dns_check() -> str:
	"""Run b2_dns_setting.py and return its combined output."""
	result = subprocess.run(
		[sys.executable, str(DNS_CHECK_SCRIPT)],
		capture_output=True,
		text=True,
		check=False,
		cwd=str(DNS_CHECK_SCRIPT.parent),
	)
	return result.stdout + result.stderr


def find_compromised_devices(output: str) -> list[dict[str, str]]:
	"""Return devices marked MISCONFIGURED by the DNS check."""
	pattern = re.compile(
		r"^(?P<name>.+?) \((?P<address>[^)]+)\) - MISCONFIGURED\s*$",
		re.MULTILINE,
	)
	return [
		{"name": match.group("name").strip(), "address": match.group("address").strip()}
		for match in pattern.finditer(output)
	]


def run_remote_command(server: dict[str, str], command: str) -> tuple[int, str, str]:
	"""Run a sudo command on a device and return exit code and output."""
	client = paramiko.SSHClient()
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	try:
		client.connect(
			hostname=server["address"],
			username=USERNAME,
			password=PASSWORD,
			timeout=SSH_TIMEOUT_SECONDS,
			banner_timeout=SSH_TIMEOUT_SECONDS,
			auth_timeout=SSH_TIMEOUT_SECONDS,
		)
		stdin, stdout, stderr = client.exec_command(
			f"sudo -S -p '' sh -c {shlex.quote(command)}",
			get_pty=True,
			timeout=SSH_TIMEOUT_SECONDS,
		)
		stdin.write(f"{PASSWORD}\n")
		stdin.flush()
		output = stdout.read().decode("utf-8", errors="replace")
		error = stderr.read().decode("utf-8", errors="replace")
		return stdout.channel.recv_exit_status(), output.strip(), error.strip()
	finally:
		client.close()


def configure_dns(server: dict[str, str]) -> bool:
	"""Set both approved DNS servers in /etc/resolv.conf."""
	command = (
		f"printf '%s\\n' 'nameserver {DNS1}' 'nameserver {DNS2}' "
		"'options timeout:2 attempts:2' > /etc/resolv.conf"
	)
	status, output, error = run_remote_command(server, command)
	if output:
		print(output)
	if error:
		print(f"Command errors: {error}")
	return status == 0


def verify_dns(server: dict[str, str]) -> bool:
	"""Verify that /etc/resolv.conf contains DNS1 and DNS2 only."""
	status, output, error = run_remote_command(server, "cat /etc/resolv.conf")
	servers = re.findall(r"^\s*nameserver\s+(\S+)", output, re.MULTILINE)
	correct = status == 0 and set(servers) == {DNS1, DNS2}
	result = "CORRECT" if correct else "INCORRECT"
	print(f"{server['name']} ({server['address']}) - {result}")
	print(f"  DNS servers: {servers or 'None'}")
	if error:
		print(f"  Verification errors: {error}")
	return correct


def main() -> int:
	devices = find_compromised_devices(run_dns_check())
	if not devices:
		print("No compromised DNS settings were found.")
		return 0

	print(f"Found {len(devices)} device(s) with compromised DNS settings.")
	configuration_results = []
	for device in devices:
		print(f"\n{'=' * 60}\n{device['name']} ({device['address']})\n{'=' * 60}")
		try:
			connected_and_configured = configure_dns(device)
			if not connected_and_configured:
				print("Unable to update DNS settings.")
			configuration_results.append(connected_and_configured)
		except Exception as exc:
			print(f"Connection/configuration failed: {exc}")
			configuration_results.append(False)

	print("\n===== DNS configuration verification =====")
	verification_results = []
	for device in devices:
		try:
			verification_results.append(verify_dns(device))
		except Exception as exc:
			print(f"{device['name']} verification failed: {exc}")
			verification_results.append(False)
	return 0 if all(configuration_results) and all(verification_results) else 1


if __name__ == "__main__":
	raise SystemExit(main())
