
"""publish_odometer_to_831l.py

This example program demonstrates how to publish the drone's odometer as a cable counter
to the PipeSonarL software used to operate the Imagenex 831L Pipe Profiling Sonar.
"""

import socket
import time
import blueye.protocol as bp
from blueye.sdk import Drone


def callback_position_estimate(
    msg_type: str, msg: bp.PositionEstimateTel, udp_socket: socket.socket
):
    """Callback for the PositionEstimateTel message."""
    odometer = msg.position_estimate.odometer * 1000  # Convert to mm
    formatted_message = f"{{,#CABLE,{odometer},mm,}}\r\n"

    udp_socket.sendto(formatted_message.encode('ascii'), (UDP_IP, UDP_PORT))
    print(f"Sent: {formatted_message.strip()}")


if __name__ == "__main__":
    # UDP configuration
    # This IP will broadcast to all devices in the 192.168.1 subnet
    UDP_IP = "192.168.1.255"

    # 1261 is the default UDP port used by the PipeSonarL software.
    UDP_PORT = 1261

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Enable broadcasting

    # Instantiate a drone object and connect to the drone
    try:
        print("Connecting to the drone...")
        my_drone = Drone(connect_as_observer=True)
    except ConnectionError:
        print("Could not connect to the drone.")
        exit(1)
    finally:
        print("Connected to the drone.")

    # Increase publishing frequenzy for the PositionEstimateTel message
    my_drone.telemetry.set_msg_publish_frequency(bp.PositionEstimateTel, 10)

    # Add a callback for the PositionEstimateTel message
    my_drone.telemetry.add_msg_callback(
        [bp.PositionEstimateTel], callback_position_estimate, udp_socket=udp_socket
    )

    # Keep the script running to receive and send messages
    try:
        print("Press Ctrl+C to exit.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        # Cleanup
        my_drone.disconnect()
        udp_socket.close()
