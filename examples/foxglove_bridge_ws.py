#!/usr/bin/env python3
import time

from blueye.sdk import Drone

import asyncio
import time
import base64
from foxglove_websocket import run_cancellable
from foxglove_websocket.server import FoxgloveServer
import sys
import inspect
from google.protobuf import descriptor_pb2
import blueye.protocol

# Declare the global variable
channel_ids = {}
global_server = None

def parse_message(payload_msg_name, data):
    global global_server
    global channel_ids

    if payload_msg_name in channel_ids:
        try:
            asyncio.run(
                global_server.send_message(channel_ids[payload_msg_name], time.time_ns(), data)
            )
        except TypeError as e:
            logger.info(f"Error sending message for {payload_msg_name}: {e}")
    else:
        logger.info(f"Warning: Channel ID not found for message type: {payload_msg_name}")


def add_file_descriptor_and_dependencies(file_descriptor, file_descriptor_set):
    """Recursively add descriptors and their dependencies to the FileDescriptorSet"""
    # Check if the descriptor is already in the FileDescriptorSet
    if file_descriptor.name not in [fd.name for fd in file_descriptor_set.file]:

        # Add the descriptor to the FileDescriptorSet
        file_descriptor.CopyToProto(file_descriptor_set.file.add())

        # Recursively add dependencies
        for file_descriptor_dep in file_descriptor.dependencies:
            add_file_descriptor_and_dependencies(file_descriptor_dep, file_descriptor_set)


def get_protobuf_descriptors(namespace):
    descriptors = {}

    # Get the module corresponding to the namespace
    module = sys.modules[namespace]

    # Iterate through all the attributes of the module
    for name, obj in inspect.getmembers(module):
        # Check if the object is a class, ends with 'Tel', and has a _meta attribute with pb
        if (
            inspect.isclass(obj)
            and name.endswith("Tel")
            and hasattr(obj, "_meta")
            and hasattr(obj._meta, "pb")
        ):
            try:
                # Access the DESCRIPTOR
                descriptor = obj._meta.pb.DESCRIPTOR

                # Create a FileDescriptorSet
                file_descriptor_set = descriptor_pb2.FileDescriptorSet()

                # Add the descriptor and its dependencies
                add_file_descriptor_and_dependencies(descriptor.file, file_descriptor_set)

                # Serialize the FileDescriptorSet to binary
                serialized_data = file_descriptor_set.SerializeToString()

                # Base64 encode the serialized data
                schema_base64 = base64.b64encode(serialized_data).decode("utf-8")

                # Store the serialized data in the dictionary
                descriptors[name] = schema_base64
            except AttributeError as e:
                logger.info(f"Skipping message: {name}: {e}")
                # Skip non-message types
                raise e

    return descriptors


async def main():
    # Initialize the drone
    myDrone = Drone()
    myDrone.telemetry.add_msg_callback([], parse_message, raw=True)

    # Specify the server's host, port, and a human-readable name
    async with FoxgloveServer("0.0.0.0", 8765, "Blueye SDK bridge") as server:
        global global_server
        global_server = server

        # Get Protobuf descriptors for all relevant message types
        namespace = "blueye.protocol"
        descriptors = get_protobuf_descriptors(namespace)

        # Register each message type as a channel
        for message_name, schema_base64 in descriptors.items():
            chan_id = await global_server.add_channel(
                {
                    "topic": f"blueye.protocol.{message_name}",  # Using the message name as the topic
                    "encoding": "protobuf",
                    "schemaName": f"blueye.protocol.{message_name}",
                    "schema": schema_base64,
                }
            )
            # Store the chan_id in the map
            channel_ids[message_name] = chan_id

        for name, chan_id in channel_ids.items():
            logger.info(f"Registered topic: blueye.protocol.{name}")

        # Keep the server running
        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
