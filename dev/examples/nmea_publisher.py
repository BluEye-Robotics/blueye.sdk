"""Forward the drone's position estimate to an NMEA UDP receiver."""

import socket
import time

import blueye.protocol as bp
from blueye.sdk import Drone

from nmea_utils import nmea_gll

# Broadcast within the surface-unit subnet. Change this to your receiver's IP if needed.
UDP_IP = "192.168.1.255"
# Do not broadcast to 10110: the drone would consume its own position output as input.
UDP_PORT = 10111


def callback_position_estimate(
    msg_type: str, msg: bp.PositionEstimateTel, udp_socket: socket.socket
):
    """Forward each position estimate, including its validity flag."""
    position = msg.position_estimate
    try:
        sentence = nmea_gll(
            position.global_position.latitude,
            position.global_position.longitude,
            position.is_valid,
        )
    except ValueError:
        return  # No usable coordinates in this sample.
    udp_socket.sendto(sentence.encode("ascii"), (UDP_IP, UDP_PORT))
    print(f"Sent: {sentence.rstrip()}")


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        with Drone(connect_as_observer=True) as drone:
            drone.telemetry.add_msg_callback(
                [bp.PositionEstimateTel], callback_position_estimate, udp_socket=udp_socket
            )
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass


if __name__ == "__main__":
    main()
