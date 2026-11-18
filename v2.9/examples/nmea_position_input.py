"""Send fresh external ROV positions from stdin to the drone's NMEA UDP input.

Each line must contain: latitude longitude A|V
Coordinates are decimal degrees; A means a valid fix and V means invalid.
Supply fresh measurements at least once per second. This script sends each line
once and does not repeat old coordinates when the source stops.

Example usage with your own positioning adapter:
    python positioning_adapter.py | python examples/nmea_position_input.py --ip 192.168.1.101

The first valid fix resets the drone's local position frame and odometer.
Do not feed the boat's GPS position or the drone's own telemetry back into this input.
"""

import argparse
import socket
import sys

from nmea_utils import nmea_gll

NMEA_INPUT_PORT = 10110


def forward_positions(lines, udp_socket: socket.socket, ip: str):
    """Convert one fresh fix per line into a unicast GPGLL datagram."""
    for line_number, line in enumerate(lines, start=1):
        try:
            latitude, longitude, status = line.split()
            if status not in ("A", "V"):
                raise ValueError("Status must be A or V")
            sentence = nmea_gll(float(latitude), float(longitude), status == "A")
        except ValueError as exc:
            print(f"Skipping line {line_number}: {exc}", file=sys.stderr)
            continue
        udp_socket.sendto(sentence.encode("ascii"), (ip, NMEA_INPUT_PORT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ip", default="192.168.1.101", help="Drone IPv4 address")
    args = parser.parse_args()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            forward_positions(sys.stdin, udp_socket, args.ip)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
