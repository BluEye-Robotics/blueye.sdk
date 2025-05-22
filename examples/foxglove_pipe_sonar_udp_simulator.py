import socket
import time
from datetime import datetime
import random
import math

"""
UDP Publisher Example
This example demonstrates how to publish messages over UDP to simulate the 831L Pipe Profiling Sonar.
The messages are generated in the format:
DD-MMM-YYYY,HH:MM:SS.mmm,X.XXX,Y.YYY,Z.ZZZ<CR><LF>
where:
- DD-MMM-YYYY: Date in day-month-year format
- HH:MM:SS.mmm: Time in hours-minutes-seconds format with milliseconds
- X.XXX: X coordinate of the sonar
- Y.YYY: Y coordinate of the sonar
- Z.ZZZ: Odometer value from the ROV
This example is intended for use with the foxglove_pipe_sonar.py example,
which listens for UDP packets and sends the data as a LaserScan message to a Foxglove client.
"""

def generate_message(odometer):
    """
    Generate a message in the format:
    DD-MMM-YYYY,HH:MM:SS.mmm,X.XXX,Y.YYY,Z.ZZZ<CR><LF>
    """
    now = datetime.now()
    timestamp = now.strftime("%d-%b-%Y,%H:%M:%S.%f")[:-3]  # Format with milliseconds
    # Generate points to form a pipe
    x = math.cos(odometer*20)
    y = math.sin(odometer*20)
    # Simulate the ROV moving forwards
    z = round(odometer, 3)
    message = f"{timestamp},{x},{y},{z}\r\n"
    return message


def udp_publisher(host="127.0.0.1", port=4040, interval=0.01):
    """
    Publish messages over UDP to the specified host and port.
    """
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    print(f"Publishing UDP messages to {host}:{port} every {interval} seconds...")
    odometer = 0.0
    i = 0
    try:
        while True:
            # Generate a message
            message = generate_message(odometer)
            print(f"Sending: {message.strip()}")

            # Send the message over UDP
            sock.sendto(message.encode("utf-8"), (host, port))

            # Wait for the specified interval
            time.sleep(interval)
            # Increment the odometer value
            i += 1
            if i % 10 == 0:
                # Update the odometer value
                odometer += 0.01

    except KeyboardInterrupt:
        print("\nStopped publishing.")
    finally:
        sock.close()


if __name__ == "__main__":
    udp_publisher()
