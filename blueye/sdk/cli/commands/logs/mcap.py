"""Conversion of .bez dive logs to Foxglove-compatible .mcap files.

Adapted from examples/foxglove_bez_to_mcap.py: the log is streamed twice — a first
pass finds the true dive start time (the drone's clock may be set mid-log, so the
last record's wall time minus its monotonic delta is the reliable anchor), and a
second pass writes every protobuf message with continuous timestamps.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ...errors import CliError

logger = logging.getLogger(__name__)


def convert_bez_to_mcap(bez_path: Path, mcap_path: Path) -> int:
    """Convert a downloaded .bez log to an .mcap file for Foxglove.

    Args:
        bez_path: The .bez file to convert.
        mcap_path: Destination .mcap path (overwritten if present).

    Returns:
        The number of messages written.

    Raises:
        CliError: When the log contains no readable records.
    """
    from mcap_protobuf.writer import Writer

    from blueye.sdk.logs import LogStream

    log_bytes = bez_path.read_bytes()

    # First pass: the last record's wall clock minus its monotonic delta gives the
    # dive start time even when the drone's clock was set partway through the log.
    last_time = None
    last_delta = None
    for last_time, last_delta, _, _ in LogStream(log_bytes):
        continue
    if last_time is None:
        raise CliError(f"{bez_path.name} contains no readable log records.")
    start_time = last_time - last_delta

    count = 0
    with mcap_path.open("wb") as mcap_file:
        writer = Writer(mcap_file)
        for _, delta, msg_type, msg in LogStream(log_bytes):
            timestamp_ns = int((start_time + delta).timestamp() * 1e9)
            writer.write_message(
                topic=msg_type.__name__,
                message=msg._pb,
                log_time=timestamp_ns,
                publish_time=timestamp_ns,
            )
            count += 1
        writer.finish()
    return count
