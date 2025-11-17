import os
import time
from pathlib import Path

import click
from mcap_protobuf.writer import Writer

from blueye.sdk.logs import LogStream


def parse_logfile(log: Path) -> LogStream:
    log_bytes = b""
    with open(log, "rb") as f:
        log_bytes = f.read()
    return LogStream(log_bytes)


@click.command(name="bez-to-mcap")
@click.argument("logfile_path", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    "output_mcap_path",
    type=click.Path(),
    help="The path to the output MCAP file.",
)
def main(logfile_path, output_mcap_path):
    """Converts a Blueye log file (.bez) to an MCAP file.

    Having the log as an mcap file makes it easy to visualize in Foxglove Studio.
    """
    if output_mcap_path is None:
        output_mcap_path = logfile_path.replace(".bez", ".mcap")

    start_time_tic = time.time()
    click.echo(f"Converting {logfile_path} to {output_mcap_path}...")

    # Prepare MCAP writer
    with open(output_mcap_path, "wb") as mcap_file:
        writer = Writer(mcap_file)

        # Read messages from the log file, deserialize, and forward the protobuf object to the MCAP file.
        path = Path(logfile_path)

        # We need to get the last message's timestamp and delta in order to get the correct start time
        # after the clock is set. The delta time is then added to the start time to get a continuous timeline in foxglove.
        last_time = 0
        last_delta = 0
        for last_time, last_delta, _, _ in parse_logfile(path):
            continue

        start_time = last_time - last_delta

        count = 0
        for unix_ts, delta, msg_type, msg in parse_logfile(path):
            writer.write_message(
                topic=msg_type.__name__,
                message=msg._pb,
                log_time=int((start_time + delta).timestamp() * 1e9),
                publish_time=int((start_time + delta).timestamp() * 1e9),
            )
            count += 1

        # Add indexes to the MCAP file
        writer.finish()

        click.echo("MCAP file successfully created!")
        click.echo(
            f"Total of messages written: {count} in {round(time.time() - start_time_tic, 3)} seconds"
        )
        click.echo(f"MCAP file name: {output_mcap_path}")
        click.echo(f"MCAP file size: {round(os.path.getsize(output_mcap_path) / 1000000, 2)} MB")
        click.echo(f"Start of dive time: {unix_ts - delta}")
        click.echo(f"Duration of dive log: {delta}")
