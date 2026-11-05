"""print_depth.py

This example program demonstrates how one can add a callback function to a telemetry message, as
well as how to adjust the frequency of that telemetry message, and how to remove the callback.
"""

import time

import blueye.protocol as bp

from blueye.sdk import Drone


def callback_depth(msg_type: str, msg: bp.DepthTel):
    """Callback for the depth telemetry message

    This function is called once for every DepthTel message received by the telemetry watcher
    """
    print(f"Got a {msg_type} message with depth: {msg.depth.value:.3f}")


if __name__ == "__main__":
    with Drone(connect_as_observer=True) as my_drone:
        # Add a callback for the DepthTel message, storing the ID for later use
        callback_id = my_drone.telemetry.add_msg_callback([bp.DepthTel], callback_depth)

        try:
            # This demonstration changes a drone-wide rate even though we are an observer.
            # Omit the rate changes if another client needs its current rate preserved.
            my_drone.telemetry.set_msg_publish_frequency(bp.DepthTel, 5)

            # Callback is triggered by a separate thread while we sleep here
            time.sleep(5)
        finally:
            my_drone.telemetry.remove_msg_callback(callback_id)

            # Restore the default, also on Ctrl-C. This is not necessarily the rate another
            # client had set before this example ran.
            my_drone.telemetry.set_msg_publish_frequency(bp.DepthTel, 10)
