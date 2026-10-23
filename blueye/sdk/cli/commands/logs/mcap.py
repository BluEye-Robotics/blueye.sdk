"""Conversion of .bez dive logs to Foxglove-compatible .mcap files.

The log is streamed twice with `LogStream`. The first pass finds the dive start time:
the drone's clock may be set partway through the log, so the last record's wall time
minus its monotonic delta is the reliable anchor. The second pass writes every record
with continuous timestamps.

Records of message types this SDK cannot decode (a drone newer than the installed
blueye.protocol, for instance) are written too, as `google.protobuf.Any` messages on a
topic named after the type, so nothing from the log is dropped and the record shows up
in Foxglove with its type URL and raw bytes.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, NamedTuple

from ...errors import CliError

logger = logging.getLogger(__name__)


class ConversionSummary(NamedTuple):
    """What `convert_bez_to_mcap` wrote."""

    #: Records written, decoded and raw alike.
    message_count: int
    #: Type URL -> number of records written raw because the SDK could not decode them.
    unknown_types: Dict[str, int]


def convert_bez_to_mcap(bez_path: Path, mcap_path: Path) -> ConversionSummary:
    """Convert a downloaded .bez log to an .mcap file for Foxglove.

    Args:
        bez_path: The .bez file to convert.
        mcap_path: Destination .mcap path (overwritten if present).

    Returns:
        The number of messages written and the types that were written raw.

    Raises:
        CliError: When the log contains no readable records.
    """
    from google.protobuf.any_pb2 import Any
    from mcap_protobuf.writer import Writer

    from blueye.sdk.logs import LogStream

    log_bytes = bez_path.read_bytes()

    # First pass: the last record's wall clock minus its monotonic delta gives the
    # dive start time even when the drone's clock was set partway through the log.
    last_time = None
    last_delta = None
    for last_time, last_delta, _, _ in LogStream(log_bytes, include_unknown=True):
        continue
    if last_time is None:
        raise CliError(f"{bez_path.name} contains no readable log records.")
    start_time = last_time - last_delta

    count = 0
    stream = LogStream(log_bytes, include_unknown=True)
    with mcap_path.open("wb") as mcap_file:
        writer = Writer(mcap_file)
        for _, delta, msg_type, msg in stream:
            timestamp_ns = int((start_time + delta).timestamp() * 1e9)
            if isinstance(msg_type, str):
                # Unknown type: msg_type is the type URL and msg the raw payload. Keep both.
                topic = msg_type.rsplit("/", 1)[-1]
                message = Any(type_url=msg_type, value=msg)
            else:
                topic = msg_type.__name__
                # blueye.protocol types are proto-plus wrappers; the google.protobuf
                # types (Empty, the wrappers) are already plain protobuf messages.
                message = getattr(msg, "_pb", msg)
            writer.write_message(
                topic=topic,
                message=message,
                log_time=timestamp_ns,
                publish_time=timestamp_ns,
            )
            count += 1
        writer.finish()
    return ConversionSummary(count, dict(stream.unknown_types))
