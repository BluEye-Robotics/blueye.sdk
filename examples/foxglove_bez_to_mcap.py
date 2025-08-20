import os
import time
from mcap_protobuf.writer import Writer
import sys
from blueye.sdk.logs import LogStream
from pathlib import Path


def parse_logfile(log: Path) -> LogStream:
    log_bytes = b""
    with open(log, "rb") as f:
        log_bytes = f.read()
    return LogStream(log_bytes)


def main(logfile_path, output_mcap_path):
    start_time_tic = time.time()
    print(f"Converting {logfile_path} to {output_mcap_path}...")

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

        print(f"MCAP file successfully created!")
        print(f"Total of messages written: {count} in {round(time.time() - start_time_tic, 3)} seconds")
        print(f"MCAP file name: {output_mcap_path}")
        print(f"MCAP file size: {round(os.path.getsize(output_mcap_path)/1000000, 2)} MB")
        print(f"Start of dive time: {unix_ts - delta}")
        print(f"Duration of dive log: {delta}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python bez_to_mcap.py <logfile.bez> [output_filename.mcap]")
        sys.exit(1)
    logfile = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1].replace(".bez", ".mcap")
    main(logfile, output)
