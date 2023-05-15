from blueye.sdk import Drone
import time


def callback_imu_raw(msg_type, msg):
    print(msg)


def callback_imu_calibrated(msg_type, msg):
    print(msg)


if __name__ == "__main__":
    my_drone = Drone()
    my_drone.set_telemetry_msg_publish_frequency("Imu1Tel", 10)
    my_drone.set_telemetry_msg_publish_frequency("Imu2Tel", 10)
    my_drone.set_telemetry_msg_publish_frequency("CalibratedImuTel", 10)

    cb_raw = my_drone.add_telemetry_msg_callback("Imu1Tel|Imu2Tel", callback_imu_raw)
    cb_calibrated = my_drone.add_telemetry_msg_callback("CalibratedImuTel", callback_imu_calibrated)

    time.sleep(3)

    my_drone.remove_telemetry_msg_callback(cb_raw)
    my_drone.remove_telemetry_msg_callback(cb_calibrated)
