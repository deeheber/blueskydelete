"""Offline eligibility checks; all Bluesky API calls are mocked."""

import logging
import os
import time
import unittest
from datetime import UTC, datetime, tzinfo
from unittest.mock import Mock, call, patch

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


if __name__ == "__main__":
    unittest.main()
