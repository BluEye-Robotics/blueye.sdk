from blueye.sdk import Drone
import time


def callback_depth(msg_type, msg):
    print(f"Got a {msg_type} message with depth: {msg.depth.value:.3f}")


if __name__ == "__main__":
    my_drone = Drone()
    cb = my_drone.add_telemetry_msg_callback("DepthTel", callback_depth)
    my_drone.set_telemetry_msg_publish_frequency("DepthTel", 5)

    time.sleep(5)
    my_drone.remove_telemetry_msg_callback(cb)
