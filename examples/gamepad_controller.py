import inputs

from blueye.sdk import Drone


class JoystickHandler:
    """Maps drone functions to joystick events"""

    def __init__(self, drone):
        self.drone = drone
        self.event_to_function_map = {
            "BTN_NORTH": self.handle_x_button,
            "BTN_WEST": self.handle_y_button,
            "BTN_EAST": self.handle_b_button,
            "BTN_SOUTH": self.handle_a_button,
            "ABS_X": self.handle_left_x_axis,
            "ABS_Y": self.handle_left_y_axis,
            "ABS_Z": self.handle_left_trigger,
            "ABS_RX": self.handle_right_x_axis,
            "ABS_RY": self.handle_right_y_axis,
            "ABS_RZ": self.handle_right_trigger,
        }

    def handle_x_button(self, value):
        """Starts/stops the video recording"""
        self.drone.camera.is_recording = value

    def handle_y_button(self, value):
        """Turns lights on or off"""
        if value:
            if self.drone.lights > 0:
                self.drone.lights = 0
            else:
                self.drone.lights = 10

    def handle_b_button(self, value):
        """Toggles autoheading"""
        if value:
            self.drone.motion.auto_heading_active = not self.drone.motion.auto_heading_active

    def handle_a_button(self, value):
        """Toggles autodepth"""
        if value:
            self.drone.motion.auto_depth_active = not self.drone.motion.auto_depth_active

    def filter_and_normalize(self, value, lower=5000, upper=32768):
        """Normalizing the joystick axis range from (default) -32768<->32678 to -1<->1

        The sticks also tend to not stop at 0 when you let them go but rather some
        low value, so we'll filter those out as well.
        """
        if -lower < value < lower:
            return 0
        elif lower <= value <= upper:
            return (value - lower) / (upper - lower)
        elif -upper <= value <= -lower:
            return (value + lower) / (upper - lower)
        else:
            return 0

    def handle_left_x_axis(self, value):
        self.drone.motion.yaw = self.filter_and_normalize(value)

    def handle_left_y_axis(self, value):
        self.drone.motion.heave = self.filter_and_normalize(value)

    def handle_right_x_axis(self, value):
        self.drone.motion.sway = self.filter_and_normalize(value)

    def handle_right_y_axis(self, value):
        self.drone.motion.surge = -self.filter_and_normalize(value)

    def handle_left_trigger(self, value):
        self.drone.motion.slow = self.filter_and_normalize(value, lower=0, upper=255)

    def handle_right_trigger(self, value):
        self.drone.motion.boost = self.filter_and_normalize(value, lower=0, upper=255)


if __name__ == "__main__":
    try:
        myDrone = Drone()
        handler = JoystickHandler(myDrone)
        while True:
            events = inputs.get_gamepad()
            for event in events:
                if event.code in handler.event_to_function_map:
                    handler.event_to_function_map[event.code](event.state)

    except KeyboardInterrupt:
        pass
