import time

import blueye.protocol as bp

from blueye.sdk import Drone


def callback_imu_raw(msg_type, msg):
    print(f"Raw {msg_type}\n{msg}")


def callback_imu_calibrated(msg_type, msg):
    print(f"{msg_type}:\n{msg}")


if __name__ == "__main__":
    my_drone = Drone()
    my_drone.telemetry.set_msg_publish_frequency(bp.Imu1Tel, 10)
    my_drone.telemetry.set_msg_publish_frequency(bp.Imu2Tel, 10)
    my_drone.telemetry.set_msg_publish_frequency(bp.CalibratedImuTel, 10)

    cb_raw = my_drone.telemetry.add_msg_callback([bp.Imu1Tel, bp.Imu2Tel], callback_imu_raw)
    cb_calibrated = my_drone.telemetry.add_msg_callback(
        [bp.CalibratedImuTel], callback_imu_calibrated
    )

    time.sleep(3)

    my_drone.telemetry.remove_msg_callback(cb_raw)
    my_drone.telemetry.remove_msg_callback(cb_calibrated)
