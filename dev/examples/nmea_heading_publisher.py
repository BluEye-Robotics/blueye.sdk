"""Forward the drone's yaw as NMEA HDT to a serial port.

Install the example dependencies with: pip install 'blueye.sdk[examples]'
"""

import math
import time

import blueye.protocol as bp
import serial
from blueye.sdk import Drone

from nmea_utils import nmea_hdt

COM_PORT = "COM2"  # Change to your serial port.
BAUD_RATE = 9600
heading = math.nan
last_attitude_time = None


def callback_attitude(msg_type: str, msg: bp.AttitudeTel):
    """Keep the latest yaw and its arrival time."""
    global heading, last_attitude_time
    heading = msg.attitude.yaw
    last_attitude_time = time.monotonic()


def main():
    global heading, last_attitude_time
    heading, last_attitude_time = math.nan, None
    try:
        with serial.Serial(COM_PORT, BAUD_RATE, timeout=1) as port:
            with Drone(connect_as_observer=True) as drone:
                drone.telemetry.add_msg_callback([bp.AttitudeTel], callback_attitude)
                # Read the existing telemetry stream; do not change the rate for other clients.
                while True:
                    if last_attitude_time is not None and time.monotonic() - last_attitude_time < 1:
                        sentence = nmea_hdt(heading)
                        if sentence is not None:
                            port.write(sentence.encode("ascii"))
                            print(f"Sent: {sentence.rstrip()}")
                    time.sleep(0.1)
    except serial.SerialException as exc:
        print(f"Serial error: {exc}")
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
