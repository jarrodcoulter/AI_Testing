"""Command line watcher for the ransomlook.io API.

This module provides a small utility that keeps track of the most recent
victims posted to ransomware groups tracked by https://www.ransomlook.io/.
It consults the public API documented at https://www.ransomlook.io/doc/ and
persists a lightweight state file so subsequent runs only display victims that
have not been seen previously.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Set

import requests

DEFAULT_BASE_URL = "https://www.ransomlook.io"
# According to the public documentation, this endpoint returns the most recent
# victims observed across all monitored leak sites. The result is paginated and
# accepts an optional ``limit`` query parameter to restrict the number of items
# returned.
DEFAULT_ENDPOINT_PATH = "/api/v1/companies/last"


class RansomlookError(RuntimeError):
    """Raised when the Ransomlook API cannot be queried successfully."""


@dataclass
class Victim:
    """Simplified representation of a victim entry returned by the API."""

    identifier: str
    group: Optional[str]
    name: Optional[str]
    published: Optional[str]
    source_url: Optional[str]

    @classmethod
    def from_payload(cls, payload: dict) -> "Victim":
        """Create a :class:`Victim` instance from an API payload.

        The API has evolved a few times, so field names may differ slightly
        depending on the endpoint. This helper attempts to normalise the
        structure by looking at the most common field names described in the
        documentation. When important data points cannot be located they are
        populated with ``None``.
        """

        identifier = _extract_identifier(payload)
        group = _first_present(payload, "group", "gang", "ransomware_group")
        name = _first_present(payload, "company", "title", "name", "victim")
        published = _first_present(
            payload,
            "date",
            "publish",
            "discovered",
            "discovered_at",
            "posted",
            "last_seen",
        )
        url = _first_present(payload, "url", "source", "site", "href")

        return cls(identifier=identifier, group=group, name=name, published=published, source_url=url)

    def summary_line(self) -> str:
        """Return a concise human readable summary for terminal output."""

        timestamp = _format_timestamp(self.published)
        victim_name = self.name or "<unknown victim>"
        group_name = f"[{self.group}] " if self.group else ""
        link = f" -> {self.source_url}" if self.source_url else ""
        return f"{timestamp} {group_name}{victim_name}{link}".strip()


def _extract_identifier(payload: dict) -> str:
    """Return a stable identifier for the entry.

    The API typically exposes one of ``id``, ``_id`` or ``slug``. When none of
    those are present a composite key is generated as a best-effort fallback so
    that new entries can still be tracked between runs.
    """

    candidates = (
        payload.get("id"),
        payload.get("_id"),
        payload.get("slug"),
        payload.get("link"),
        payload.get("url"),
    )
    for candidate in candidates:
        if candidate:
            return str(candidate)

    group = _first_present(payload, "group", "gang", "ransomware_group") or "unknown"
    name = _first_present(payload, "company", "title", "name", "victim") or "unknown"
    published = _first_present(
        payload,
        "date",
        "publish",
        "discovered",
        "discovered_at",
        "posted",
        "last_seen",
    )
    fallback = f"{group}::{name}::{published or 'na'}"
    return fallback


def _first_present(payload: dict, *keys: str) -> Optional[str]:
    for key in keys:
        value = payload.get(key)
        if value:
            return value
    return None


def _format_timestamp(value: Optional[str]) -> str:
    if not value:
        return "[unknown time]"

    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            continue

    return value


class RansomlookClient:
    """Thin wrapper around the ransomlook.io HTTP API."""

    def __init__(self, base_url: str = DEFAULT_BASE_URL, endpoint_path: str = DEFAULT_ENDPOINT_PATH):
        if not base_url.endswith("/"):
            base_url = base_url.rstrip("/")
        self.base_url = base_url
        self.endpoint_path = endpoint_path.lstrip("/")

    def fetch_latest_victims(self, limit: int) -> List[Victim]:
        url = f"{self.base_url}/{self.endpoint_path}"
        try:
            response = requests.get(url, params={"limit": limit}, timeout=30)
        except requests.RequestException as exc:  # pragma: no cover - defensive
            raise RansomlookError(f"Unable to query {url}: {exc}") from exc

        if response.status_code != 200:
            raise RansomlookError(
                f"Unexpected status code {response.status_code} when requesting {url}: {response.text[:200]}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise RansomlookError("API response did not contain valid JSON") from exc

        items: Iterable[dict]
        if isinstance(payload, dict):
            items = payload.get("items") or payload.get("data") or payload.values()
            if isinstance(items, dict):
                items = items.values()
            if not isinstance(items, Iterable):
                raise RansomlookError("Could not locate list of victims in API response")
        elif isinstance(payload, list):
            items = payload
        else:
            raise RansomlookError("Unsupported API response format")

        victims = []
        for entry in items:
            if not isinstance(entry, dict):
                continue
            victims.append(Victim.from_payload(entry))
        return victims


def load_state(path: Path) -> Set[str]:
    if not path.exists():
        return set()
    try:
        content = json.loads(path.read_text())
    except json.JSONDecodeError:
        return set()
    if isinstance(content, dict):
        identifiers = content.get("identifiers")
    else:
        identifiers = content
    if not isinstance(identifiers, Sequence):
        return set()
    return {str(item) for item in identifiers}


def store_state(path: Path, identifiers: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"identifiers": list(identifiers)}, indent=2))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="List new victims published on ransomlook.io")
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="Base URL of the ransomlook instance (default: %(default)s)",
    )
    parser.add_argument(
        "--endpoint",
        default=DEFAULT_ENDPOINT_PATH,
        help="API endpoint that yields the most recent victims (default: %(default)s)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Maximum number of victims to retrieve per run (default: %(default)s)",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=Path(os.environ.get("RANSOMLOOK_STATE", Path.home() / ".cache" / "ransomlook_watcher.json")),
        help="Location of the JSON file used to remember previously seen victims",
    )
    parser.add_argument(
        "--max-state",
        type=int,
        default=500,
        help="Maximum number of identifiers to keep in the state file (default: %(default)s)",
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Display all victims returned by the API instead of only new entries",
    )

    args = parser.parse_args(argv)

    client = RansomlookClient(base_url=args.base_url, endpoint_path=args.endpoint)
    victims = client.fetch_latest_victims(limit=args.limit)

    seen = load_state(args.state_file)
    new_victims = [victim for victim in victims if victim.identifier not in seen]

    if args.show_all:
        entries_to_display = victims
    else:
        entries_to_display = new_victims

    if entries_to_display:
        print("Latest victims:")
        for victim in entries_to_display:
            print(f" - {victim.summary_line()}")
    else:
        print("No new victims detected.")

    updated_ids = list(seen)
    for victim in new_victims:
        updated_ids.append(victim.identifier)
    if len(updated_ids) > args.max_state:
        updated_ids = updated_ids[-args.max_state :]

    store_state(args.state_file, updated_ids)

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
