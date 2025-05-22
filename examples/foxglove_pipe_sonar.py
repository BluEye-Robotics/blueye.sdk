import math
import json  # Import JSON for encoding the LaserScan data
from foxglove_websocket.server import FoxgloveServer
import asyncio
import time
import socket

# This example shows how to create a Foxglove server that listens for UDP packets
# and sends the data as a LaserScan message to a Foxglove client.
# The server listens on port 4040 for incoming UDP packets from the 831L Pipe Profiling Sonar
# The incoming message format is: # DD-MMM-YYYY,HH:MM:SS.mmm,X.XXX,Y.YYY,Z.ZZZ<CR><LF>
# The points can be viewed as a point cloud in the Foxglove client with the "Decay time" feature.


# Returns the radius and angle from the x and y coordinates of the sonar, to fit into the LaserScan message.
def get_radius_and_angle_from_xy(x, y):
    """Calculate the radius and angle from x and y coordinates."""
    radius = math.hypot(x, y)
    angle = math.atan2(y, x)  # Angle in radians
    return radius, angle


async def start_server():
    # Specify the server's host, port, and a human-readable name
    async with FoxgloveServer("0.0.0.0", 8765, "Blueye SDK bridge") as server:
        print("Starting Foxglove server...")
        global global_server
        global_server = server

        # Register a channel for foxglove.FrameTransform
        transform_topic = await global_server.add_channel(
            {
                "topic": "frame_transform",  # Topic name for the FrameTransform message
                "encoding": "json",  # JSON encoding
                "schemaName": "foxglove.FrameTransform",  # Schema name for FrameTransform
                "schema": "",  # No schema required for JSON encoding
            }
        )

        # Register a channel for foxglove.LaserScan
        laser_scan_topic = await global_server.add_channel(
            {
                "topic": "laser_scan",  # Topic name for the LaserScan message
                "encoding": "json",  # JSON encoding
                "schemaName": "foxglove.LaserScan",  # Schema name for LaserScan
                "schema": "",  # No schema required for JSON encoding
            }
        )

        # Start the UDP listener
        port = 4040  # Port to listen on
        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Bind the socket to all interfaces and the specified port
        sock.bind(("0.0.0.0", port))

        # Set the socket to non-blocking mode
        sock.setblocking(False)
        # Set a timeout for the socket
        # sock.settimeout(3)  # Timeout in seconds

        print(f"Listening for UDP packets on port {port}...")
        odometer = -1.0
        points = []
        # The bool can be used to accumulate multiple points in one LaserScan message
        stack_points_until_odometer_change = False

        while True:
            try:
                data, addr = sock.recvfrom(4096)  # buffer size is 4096 bytes
                # Parse the message and print the values
                x, y, z = parse_message(data.decode(errors="replace"))
                if x is not None and y is not None and z is not None:

                    points.append((x, y, z))
                    if not stack_points_until_odometer_change or odometer > 0 and odometer != z:
                        odometer = z
                        laser_scan = create_laser_scan_message(points)
                        # Serialize the LaserScan data to JSON and encode it as bytes
                        message = json.dumps(laser_scan).encode("utf-8")
                        # Send the message on the registered channel
                        if server is not None and laser_scan_topic is not None:
                            await server.send_message(
                                laser_scan_topic, int(time.time() * 1e9), message
                            )
                        else:
                            print("Server or topic not initialized")
                        points = []
                    elif odometer < 0:
                        odometer = z
            except BlockingIOError:
                # No data received, continue listening
                await asyncio.sleep(0.1)

            # Update position of the ROV relative to the world frame.
            frame_transform = create_free_transform_message(odometer)

            # Serialize the FrameTransform data to JSON and encode it as bytes
            ft_message_transform = json.dumps(frame_transform).encode("utf-8")
            await global_server.send_message(
                transform_topic, int(time.time() * 1e9), ft_message_transform
            )


def create_free_transform_message(odometer):
    """
    Create a FrameTransform message.
    This message is used to transform the laser scan data to the world frame.
    In this case, the child frame is the ROV and the parent frame is the world frame.
    The translation is the odometer value in the x direction and 0 in the y and z directions.
    The rotation is the identity quaternion (no rotation).
    """
    frame_transform = {
        "timestamp": {
            "sec": int(time.time()),
            "nsec": int((time.time() % 1) * 1e9),
        },
        "parent_frame_id": "world",  # Parent frame
        "child_frame_id": "ROV",  # Child frame
        "translation": {
            "x": odometer,
            "y": 0.0,
            "z": 0.0,
        },  # Translation in meters
        "rotation": {
            "x": 0.0,
            "y": 0.0,
            "z": 0.0,
            "w": 0.0,
        },  # Identity quaternion (no rotation)
    }
    return frame_transform


def create_laser_scan_message(point_buffer):
    odometer = point_buffer[0][2]  # Get the odometer value from the first z coordinate
    # Generate 10 points for the laser scan
    ranges = []
    intensities = []
    start_angle = None
    end_angle = None

    for [x, y, _] in point_buffer:

        radius, current_angle = get_radius_and_angle_from_xy(-y, -x)

        if start_angle is None:
            start_angle = current_angle
        end_angle = current_angle

        ranges.append(radius)
        intensities.append(current_angle)  # Optional: Intensity for each point

    laser_scan = {
        "timestamp": {
            "sec": int(time.time()),
            "nsec": int((time.time() % 1) * 1e9),
        },
        "frame_id": "world",  # Reference frame
        "pose": {
            "position": {"x": odometer, "y": 0.0, "z": 0.0},
            "orientation": {"x": 0.0, "y": 0.7071, "z": 0.0, "w": 0.7071},
        },
        "start_angle": start_angle,  # Start angle in radians
        "end_angle": end_angle,  # End angle in radians
        "ranges": ranges,  # Distances for each angle
        "intensities": intensities,  # Intensity for each point
    }
    return laser_scan


def parse_message(message):
    """
    Parse the incoming message in the format:
    DD-MMM-YYYY,HH:MM:SS.mmm,X.XXX,Y.YYY,Z.ZZZ<CR><LF>
    The message is split by commas and the X.XXX, Y.YYY, Z.ZZZ values are extracted
    and returned as floats. The function also handles errors and prints the message.
    The x and y is the point from the sonar, and z is the odometer value.
    If the message is not in the correct format, it returns None for x, y, and z.
    """
    try:
        # Remove <CR><LF> and split the message by commas
        parts = message.strip().split(",")
        if len(parts) != 5:
            raise ValueError("Invalid message format")

        # Extract X.XXX, Y.YYY, Z.ZZZ
        x = float(parts[2])
        y = float(parts[3])
        z = float(parts[4])

        print(f"message: {message}")
        return x, y, z
    except Exception as e:
        print(f"Failed to parse message: {message}. Error: {e}")
        return None, None, None


async def main():
    """
    Start the foxglove server,
    and listen for incoming UDP packets,
    and send the data as a LaserScan message to the Foxglove client.
    """
    await start_server()


if __name__ == "__main__":
    asyncio.run(main())
