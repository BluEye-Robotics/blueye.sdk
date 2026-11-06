"""print_imu.py

Print the drone's IMU telemetry for a few seconds. Every model publishes Imu1Tel, Imu2Tel and
CalibratedImuTel. Only the X3 Ultra and X7 have the high-precision IMU behind ImuHpTel and
CalibratedImuHpTel, so on other models that callback never runs.
"""

import time

import blueye.protocol as bp

from blueye.sdk import Drone


def callback_imu_raw(msg_type, msg):
    print(f"Raw {msg_type}\n{msg}")


def callback_imu_calibrated(msg_type, msg):
    print(f"{msg_type}:\n{msg}")


def callback_imu_high_precision(msg_type, msg):
    print(f"High-precision {msg_type}:\n{msg}")


if __name__ == "__main__":
    with Drone(connect_as_observer=True) as my_drone:
        # Use the current telemetry rates without changing them for the pilot.
        my_drone.telemetry.add_msg_callback([bp.Imu1Tel, bp.Imu2Tel], callback_imu_raw)
        my_drone.telemetry.add_msg_callback([bp.CalibratedImuTel], callback_imu_calibrated)
        my_drone.telemetry.add_msg_callback(
            [bp.ImuHpTel, bp.CalibratedImuHpTel], callback_imu_high_precision
        )
        time.sleep(3)
