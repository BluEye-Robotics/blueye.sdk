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
    start_time = time.time()
    print(f"Converting {logfile_path} to {output_mcap_path}...")

    # Prepare MCAP writer
    with open(output_mcap_path, "wb") as mcap_file:
        writer = Writer(mcap_file)

        # Read messages from the log file, deserialize, and forward the protobuf object to the MCAP file.
        path = Path(logfile_path)
        log_stream = parse_logfile(path)

        count = 0
        for unix_ts, delta, msg_type, msg in log_stream:
            writer.write_message(
                topic=msg_type.__name__,
                message=msg._pb,
                log_time=int(unix_ts.timestamp() * 1e9),
                publish_time=int(unix_ts.timestamp() * 1e9),
            )
            count += 1

        # Add indexes to the MCAP file
        writer.finish()

        print(f"MCAP file successfully created!")
        print(f"Total of messages written: {count} in {round(time.time() - start_time, 3)} seconds")
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
