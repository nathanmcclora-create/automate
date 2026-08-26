"""Create and verify a ticket through the Helpdesk API.

The API is expected to expose ``GET /api/tickets`` and
``POST /api/tickets``.  The token is included here because this is a
coursework scaffold; in a production script, load it from a secret store or
environment variable instead.
"""

import argparse
import json
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_HOST = "api.d522.wgu.internal"
API_PORT = 5000
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"
API_TOKEN = "vGkbXkGLqQSo7YLflp9DutuG8st4xdPPF7wnTcwB0FE"
TICKETS_PATH = "/api/tickets"
REQUEST_TIMEOUT_SECONDS = 10


class HelpdeskAPIError(RuntimeError):
	"""Raised when the Helpdesk API cannot complete a request."""


class HelpdeskAPI:
	def __init__(self, base_url: str = API_BASE_URL, token: str = API_TOKEN):
		self.base_url = base_url.rstrip("/")
		self.token = token

	def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
		body = json.dumps(payload).encode("utf-8") if payload is not None else None
		request = Request(
			f"{self.base_url}{path}",
			data=body,
			method=method,
			headers={
				"Accept": "application/json",
				"Authorization": f"Bearer {self.token}",
				"Content-Type": "application/json",
			},
		)

		try:
			with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
				response_body = response.read().decode("utf-8")
		except HTTPError as exc:
			details = exc.read().decode("utf-8", errors="replace")
			raise HelpdeskAPIError(f"{method} {path} failed ({exc.code}): {details}") from exc
		except URLError as exc:
			raise HelpdeskAPIError(f"Could not connect to {self.base_url}: {exc.reason}") from exc

		if not response_body:
			return None
		try:
			return json.loads(response_body)
		except json.JSONDecodeError as exc:
			raise HelpdeskAPIError(f"{method} {path} returned invalid JSON") from exc

	def list_tickets(self) -> Any:
		return self._request("GET", TICKETS_PATH)

	def create_ticket(self, title: str, description: str) -> Any:
		# Adjust these field names here if the deployed API documents a
		# different ticket schema.
		return self._request(
			"POST",
			TICKETS_PATH,
			{
				"title": title,
				"description": description,
				"priority": "medium",
				"status": "open",
			},
		)


def ticket_id(ticket_response: Any) -> Any:
	"""Extract a ticket identifier from common API response shapes."""
	if not isinstance(ticket_response, dict):
		return None
	if ticket_response.get("id") is not None:
		return ticket_response["id"]
	if ticket_response.get("ticket_id") is not None:
		return ticket_response["ticket_id"]
	nested_ticket = ticket_response.get("ticket")
	if isinstance(nested_ticket, dict):
		return nested_ticket.get("id", nested_ticket.get("ticket_id"))
	return None


def ticket_is_present(tickets_response: Any, created_ticket: Any) -> bool:
	"""Check that the create response appears in the ticket collection."""
	created_id = ticket_id(created_ticket)
	if created_id is None:
		return False

	tickets = tickets_response.get("tickets", tickets_response) if isinstance(tickets_response, dict) else tickets_response
	if not isinstance(tickets, list):
		return False
	return any(ticket_id(ticket) == created_id for ticket in tickets)


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--title", default="Helpdesk API connectivity test")
	parser.add_argument(
		"--description",
		default="Test ticket created by c2_alerts_script.py to verify Helpdesk API access.",
	)
	args = parser.parse_args()

	api = HelpdeskAPI()
	try:
		api.list_tickets()
		print("Helpdesk API authentication and connectivity: OK")

		created_ticket = api.create_ticket(args.title, args.description)
		created_id = ticket_id(created_ticket)
		if created_id is None:
			raise HelpdeskAPIError(
				"Ticket creation returned successfully, but no ticket id was found in the response."
			)
		print(f"Ticket created: {created_id}")

		current_tickets = api.list_tickets()
		if not ticket_is_present(current_tickets, created_ticket):
			raise HelpdeskAPIError(f"Created ticket {created_id} was not found in GET /api/tickets")
		print(f"Ticket verification: OK (ticket {created_id} is present)")
		return 0
	except HelpdeskAPIError as exc:
		print(f"Helpdesk API check failed: {exc}", file=sys.stderr)
		return 1


if __name__ == "__main__":
	raise SystemExit(main())
