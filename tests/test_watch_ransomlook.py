"""Tests for the ransomlook watcher utility."""
from __future__ import annotations

import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock, TestCase

from ransomlook_watcher.watch_ransomlook import (
    RansomlookClient,
    Victim,
    load_state,
    main,
    store_state,
)


class VictimTests(TestCase):
    def test_from_payload_handles_missing_fields(self) -> None:
        payload = {
            "company": "Acme Corp",
            "group": "example",
            "date": "2024-01-02T03:04:05Z",
        }

        victim = Victim.from_payload(payload)

        self.assertEqual(victim.identifier, "example::Acme Corp::2024-01-02T03:04:05Z")
        self.assertEqual(victim.group, "example")
        self.assertEqual(victim.name, "Acme Corp")
        self.assertEqual(victim.published, "2024-01-02T03:04:05Z")
        self.assertIsNone(victim.source_url)
        self.assertIn("Acme Corp", victim.summary_line())


class ClientTests(TestCase):
    @mock.patch("ransomlook_watcher.watch_ransomlook.requests.get")
    def test_fetch_latest_victims_parses_entries(self, mock_get: mock.Mock) -> None:
        response = mock.Mock(status_code=200)
        response.json.return_value = {
            "items": [
                {
                    "id": "abc",
                    "group": "group1",
                    "company": "Example Inc",
                    "date": "2024-03-01T12:00:00Z",
                    "url": "https://example.com/post",
                }
            ]
        }
        mock_get.return_value = response

        client = RansomlookClient(base_url="https://test", endpoint_path="/api/latest")
        victims = client.fetch_latest_victims(limit=10)

        mock_get.assert_called_once_with(
            "https://test/api/latest", params={"limit": 10}, timeout=30
        )
        self.assertEqual(len(victims), 1)
        self.assertEqual(victims[0].identifier, "abc")
        self.assertEqual(victims[0].group, "group1")


class StateTests(TestCase):
    def test_store_and_load_state_roundtrip(self) -> None:
        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "state.json"
            store_state(path, ["one", "two"])

            loaded = load_state(path)

            self.assertEqual(loaded, {"one", "two"})


class MainTests(TestCase):
    @mock.patch("ransomlook_watcher.watch_ransomlook.requests.get")
    def test_main_lists_new_victims_and_updates_state(self, mock_get: mock.Mock) -> None:
        response = mock.Mock(status_code=200)
        response.json.return_value = [
            {
                "id": "first",
                "group": "group-one",
                "company": "Alpha",
                "date": "2024-04-01T01:02:03Z",
            },
            {
                "id": "second",
                "group": "group-two",
                "company": "Beta",
                "date": "2024-04-02T01:02:03Z",
            },
        ]
        mock_get.return_value = response

        with TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "state.json"
            args = ["--limit", "5", "--state-file", str(state_file)]

            with mock.patch("sys.stdout", new=io.StringIO()) as fake_stdout:
                exit_code = main(args)

            output = fake_stdout.getvalue()

            self.assertEqual(exit_code, 0)
            self.assertIn("Latest victims:", output)
            self.assertIn("Alpha", output)
            self.assertIn("Beta", output)

            data = json.loads(state_file.read_text())
            self.assertEqual(data["identifiers"], ["first", "second"])

            # Run again with the stored state to ensure no new victims are reported.
            with mock.patch("sys.stdout", new=io.StringIO()) as fake_stdout:
                exit_code = main(args)

            self.assertEqual(exit_code, 0)
            self.assertIn("No new victims detected.", fake_stdout.getvalue())
