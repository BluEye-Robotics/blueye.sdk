import base64
import os
import time
from mcap.writer import Writer
import sys
import inspect
from google.protobuf import descriptor_pb2
from blueye.sdk.logs import LogFile, LogStream
from pathlib import Path


def add_file_descriptor_and_dependencies(file_descriptor, file_descriptor_set):
    if file_descriptor.name not in [fd.name for fd in file_descriptor_set.file]:
        file_descriptor.CopyToProto(file_descriptor_set.file.add())
        for file_descriptor_dep in file_descriptor.dependencies:
            add_file_descriptor_and_dependencies(file_descriptor_dep, file_descriptor_set)

def get_protobuf_descriptors(namespace):
    descriptors = {}
    module = sys.modules[namespace]
    for name, obj in inspect.getmembers(module):
        if (
            inspect.isclass(obj)
            and name.endswith("Tel") or name.endswith("Ctrl") or name.endswith("Req") or name.endswith("Rep")
            and hasattr(obj, "_meta")
            and hasattr(obj._meta, "pb")
        ):
            try:
                descriptor = obj._meta.pb.DESCRIPTOR
                file_descriptor_set = descriptor_pb2.FileDescriptorSet()
                add_file_descriptor_and_dependencies(descriptor.file, file_descriptor_set)
                serialized_data = file_descriptor_set.SerializeToString()
                schema_base64 = base64.b64encode(serialized_data).decode("utf-8")
                descriptors[name] = schema_base64
            except AttributeError as e:
                print(f"Skipping message: {name}: {e}")
    return descriptors


def parse_logfile(log: LogFile | Path):
    log_bytes = b""
    if isinstance(log, Path):
        with open(log, "rb") as f:
            log_bytes = f.read()
    return LogStream(log_bytes, deserialize_msg=False)


def main(logfile_path, output_mcap_path):
    # Prepare MCAP writer
    start_time = time.time()
    print(f"Converting {logfile_path} to {output_mcap_path}...")
    with open(output_mcap_path, "wb") as mcap_file:
        writer = Writer(mcap_file)
        writer.start(profile="x-custom", library="my-writer-v1")

        namespace = "blueye.protocol"
        descriptors = get_protobuf_descriptors(namespace)
        channel_ids = {}

        # Register schemas and channels for each message type
        schema_ids = {}
        for message_name, schema_base64 in descriptors.items():
            schema_id = writer.register_schema(
                name=f"blueye.protocol.{message_name}",
                encoding="protobuf",
                data=base64.b64decode(schema_base64),
            )
            schema_ids[message_name] = schema_id
            channel_id = writer.register_channel(
                schema_id=schema_id,
                topic=f"blueye.protocol.{message_name}",
                message_encoding="protobuf",
            )
            channel_ids[message_name] = channel_id

        print("Schemas and channels registered.")

        # Read messages from the log file and forward the serialized data to the MCAP file.
        path = Path(logfile_path)
        log_stream = parse_logfile(path)

        count = 0
        for record in log_stream:
            unix_ts, delta, msg_type, msg = record

            msg = msg.pb() if hasattr(msg, "pb") else msg  # Ensure we have the protobuf message

            msg_type_name = msg_type.__name__

            if msg_type_name in channel_ids:
                channel_id = channel_ids[msg_type_name]
                writer.add_message(
                    channel_id=channel_id,
                    log_time=int(unix_ts.timestamp() * 1e9) if hasattr(unix_ts, "timestamp") else int(unix_ts),
                    publish_time=int(unix_ts.timestamp() * 1e9) if hasattr(unix_ts, "timestamp") else int(unix_ts),
                    data=msg,  # forward the serialized message data
                )
                count += 1
            else:
                print(f"Skipping unknown message type: {msg_type}")
        writer.finish()

        print(f"MCAP file successfully created!")
        print(f"Total of messages written: {count} in {round(time.time() - start_time, 3)} seconds")
        print(f"MCAP file name: {output_mcap_path}")
        print(f"MCAP file size: {round(os.path.getsize(output_mcap_path)/1000000, 2)} MB")
        print(f"Start of dive time: {unix_ts - delta}")
        print(f"Duration of dive log: {delta}")

        return channel_ids


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python bez_to_mcap.py <logfile.bez> [output_filename.mcap]")
        sys.exit(1)
    logfile = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1].replace(".bez", ".mcap")
    main(logfile, output)
