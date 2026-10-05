"""Offline cleanup checks; all Bluesky API calls are mocked."""

import logging
import os
import time
import unittest
from datetime import UTC, datetime, tzinfo
from unittest.mock import Mock, call, patch

from atproto import exceptions

import main

NOW = datetime(2026, 10, 4, 12, tzinfo=UTC)

# All eligible fixtures represent the same UTC cutoff or an older instant.
ELIGIBLE_TIMESTAMPS = (
    "2026-10-03T11:59:59.999999Z",
    "2026-10-03T12:00:00.000Z",
    "2026-10-03T12:00:00Z",
    "2026-10-03T12:00:00+00:00",
    "2026-10-03T14:00:00+02:00",
    "2026-10-03T05:00:00-07:00",
    "2026-10-03T14:00:00.000000+02:00",
    "2026-10-03T05:00:00.000000-07:00",
)
NEWER_TIMESTAMPS = (
    "2026-10-03T12:00:00.000001Z",
    "2026-10-03T12:00:00.001Z",
    "2026-10-03T14:00:00.000001+02:00",
    "2026-10-03T05:00:00.000001-07:00",
)


class CleanupEligibilityTests(unittest.TestCase):
    """Exercise eligibility through the collection processing API."""

    def setUp(self) -> None:
        self.client = Mock()
        self.logger = Mock(spec=logging.Logger)
        self.environment = patch.dict(os.environ, {"DAYS_AGO": "1"})
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def process(self, collection: str, timestamps: tuple[str, ...]) -> Mock:
        """Process fixture records using a fixed instant and mocked API.

        Args:
            collection: Collection to process.
            timestamps: Creation timestamps in API response order.

        Returns:
            Mock clock for checking timestamp parsing.
        """
        records = [
            Mock(
                uri=f"at://test/{collection}/{index}",
                value=Mock(created_at=timestamp),
            )
            for index, timestamp in enumerate(timestamps)
        ]
        self.client.com.atproto.repo.list_records.return_value = Mock(
            records=records, cursor=None
        )

        # A naive now() must reflect local time to expose the original bug.
        def fixed_now(tz: tzinfo | None = None) -> datetime:
            if tz is None:
                return NOW.astimezone().replace(tzinfo=None)
            return NOW.astimezone(tz)

        with patch.object(main, "datetime", wraps=datetime) as clock:
            clock.now.side_effect = fixed_now
            main.fetch_and_process(
                collection, self.client, "test", self.logger
            )
        return clock

    @unittest.skipUnless(hasattr(time, "tzset"), "requires POSIX tzset")
    def test_eligibility_is_independent_of_local_timezone(self) -> None:
        for timezone in ("UTC0", "PST8PDT", "JST-9"):
            for collection in ("post", "repost", "like"):
                with self.subTest(timezone=timezone, collection=collection):
                    self.client.reset_mock()
                    try:
                        with patch.dict(
                            os.environ, {"TZ": timezone, "DRY_RUN": "false"}
                        ):
                            time.tzset()
                            clock = self.process(
                                collection,
                                ELIGIBLE_TIMESTAMPS + NEWER_TIMESTAMPS[:1],
                            )
                    finally:
                        time.tzset()
                    self.assertEqual(
                        getattr(
                            self.client, f"delete_{collection}"
                        ).call_args_list,
                        [
                            call(f"at://test/{collection}/{index}")
                            for index in range(len(ELIGIBLE_TIMESTAMPS))
                        ],
                    )
                    self.assertEqual(
                        clock.fromisoformat.call_args_list,
                        [
                            call(timestamp)
                            for timestamp in ELIGIBLE_TIMESTAMPS
                            + NEWER_TIMESTAMPS[:1]
                        ],
                    )

    def test_newer_offset_timestamps_are_ineligible(self) -> None:
        with patch.dict(os.environ, {"DRY_RUN": "false"}):
            for timestamp in NEWER_TIMESTAMPS:
                with self.subTest(timestamp=timestamp):
                    self.process("post", (timestamp,))
                    self.client.delete_post.assert_not_called()

    def test_dry_run_is_the_default(self) -> None:
        os.environ.pop("DRY_RUN", None)
        self.process("post", ELIGIBLE_TIMESTAMPS)
        self.client.delete_post.assert_not_called()
        self.assertEqual(
            sum(
                args[0].startswith("🔄 DRY RUN: Would delete")
                for args, _ in self.logger.warning.call_args_list
            ),
            len(ELIGIBLE_TIMESTAMPS),
        )

    def test_timestamp_without_timezone_is_rejected(self) -> None:
        with patch.dict(os.environ, {"DRY_RUN": "false"}):
            with self.assertRaisesRegex(ValueError, "include a timezone"):
                self.process("post", ("2026-10-03T12:00:00",))
        self.client.delete_post.assert_not_called()


class CleanupOutcomeTests(unittest.TestCase):
    """Verify counts, continuation, and exit status with mocked API calls."""

    def setUp(self) -> None:
        self.client = Mock()
        self.logger = Mock(spec=logging.Logger)
        self.records = {
            collection: [
                Mock(
                    uri=f"at://test/{collection}/{index}",
                    value=Mock(created_at="2000-01-01T00:00:00Z"),
                )
                for index in range(2 if collection == "post" else 1)
            ]
            for collection in ("post", "repost", "like")
        }

        def list_records(params: dict[str, object]) -> Mock:
            collection = str(params["collection"]).removeprefix(
                main.COLLECTION_PREFIX
            )
            return Mock(records=self.records[collection], cursor=None)

        self.client.com.atproto.repo.list_records.side_effect = list_records
        self.enterContext(
            patch.dict(
                os.environ,
                {
                    "USERNAME": "test",
                    "PASSWORD": "mock-password",
                    "DAYS_AGO": "1",
                    "DRY_RUN": "false",
                },
                clear=True,
            )
        )
        self.enterContext(
            patch.object(
                main, "authenticate_client", return_value=(self.client, "test")
            )
        )
        self.enterContext(
            patch.object(main, "setup_logging", return_value=self.logger)
        )

    def assert_all_deletions_attempted(self) -> None:
        """Check that every collection's records reached its delete API."""
        for collection, records in self.records.items():
            self.assertEqual(
                getattr(self.client, f"delete_{collection}").call_args_list,
                [call(record.uri) for record in records],
            )

    def test_mixed_failures_continue_and_exit_nonzero(self) -> None:
        self.client.delete_post.side_effect = [
            exceptions.AtProtocolError("mock post failure"),
            None,
        ]
        self.client.delete_like.side_effect = RuntimeError("mock like failure")

        with self.assertRaises(SystemExit) as exit_context:
            main.main()

        self.assertEqual(exit_context.exception.code, 1)
        self.assert_all_deletions_attempted()
        for summary in (
            "Posts: 1 deleted, 1 failed",
            "Reposts: 1 deleted, 0 failed",
            "Likes: 0 deleted, 1 failed",
        ):
            self.logger.info.assert_any_call(summary)
        self.logger.error.assert_any_call(
            "Cleanup incomplete: 2 deleted, 2 failed"
        )

    def test_all_deletions_fail(self) -> None:
        for collection in self.records:
            getattr(self.client, f"delete_{collection}").side_effect = (
                exceptions.AtProtocolError("mock deletion failure")
            )

        with self.assertRaises(SystemExit) as exit_context:
            main.main()

        self.assertEqual(exit_context.exception.code, 1)
        self.assert_all_deletions_attempted()
        self.logger.error.assert_any_call(
            "Cleanup incomplete: 0 deleted, 4 failed"
        )

    def test_successful_and_empty_runs_return_normally(self) -> None:
        for empty in (False, True):
            with self.subTest(empty=empty):
                self.client.reset_mock()
                self.logger.reset_mock()
                if empty:
                    for records in self.records.values():
                        records.clear()

                main.main()

                self.assert_all_deletions_attempted()
                self.logger.error.assert_not_called()
                self.logger.info.assert_any_call(
                    f"Cleanup total: {0 if empty else 4} deleted, 0 failed"
                )

    def test_explicit_and_default_dry_runs(self) -> None:
        for dry_run in ("true", None):
            with self.subTest(dry_run=dry_run):
                self.logger.reset_mock()
                if dry_run is None:
                    os.environ.pop("DRY_RUN")
                else:
                    os.environ["DRY_RUN"] = dry_run

                main.main()

                for collection, records in self.records.items():
                    getattr(
                        self.client, f"delete_{collection}"
                    ).assert_not_called()
                    self.logger.info.assert_any_call(
                        f"🔄 DRY RUN: {len(records)} {collection}s would be deleted"
                    )
                self.logger.info.assert_any_call(
                    "🔄 DRY RUN total: 4 records would be deleted"
                )
                self.logger.error.assert_not_called()

    def test_serialization_failure_counts_and_continues(self) -> None:
        self.records["post"][0].model_dump_json.side_effect = ValueError(
            "mock serialization failure"
        )

        result = main.fetch_and_process(
            "post", self.client, "test", self.logger
        )

        self.assertEqual(result, main.CleanupResult(deleted=1, failed=1))
        self.client.delete_post.assert_called_once_with(
            self.records["post"][1].uri
        )

    def test_fetch_failure_still_exits_immediately(self) -> None:
        self.client.com.atproto.repo.list_records.side_effect = (
            exceptions.AtProtocolError("mock fetch failure")
        )

        with self.assertRaises(SystemExit) as exit_context:
            main.main()

        self.assertEqual(exit_context.exception.code, 1)
        self.client.com.atproto.repo.list_records.assert_called_once()
        for collection in self.records:
            getattr(self.client, f"delete_{collection}").assert_not_called()


if __name__ == "__main__":
    unittest.main()
