import signal

from xbox360controller import Xbox360Controller

from blueye.sdk import Pioneer


class JoystickHandler:
    def __init__(self, pioneer):
        self.pioneer = pioneer

    def button_a_pressed(self, button):
        """Toggle lights when button A is pressed"""
        if self.pioneer.lights > 0:
            self.pioneer.lights = 0
        else:
            self.pioneer.lights = 10

    def left_axis_moved(self, axis):
        """Map left joystick to heave and yaw"""
        self.pioneer.motion.heave = axis.y
        self.pioneer.motion.yaw = axis.x

    def right_axis_moved(self, axis):
        """Map right joystick to surge and sway"""
        self.pioneer.motion.surge = axis.y
        self.pioneer.motion.sway = axis.x


try:
    p = Pioneer()
    jh = JoystickHandler(p)
    with Xbox360Controller(0, axis_threshold=0) as controller:
        # Button A events
        controller.button_a.when_pressed = jh.button_a_pressed
        # Left and right axis move event
        controller.axis_l.when_moved = jh.left_axis_moved
        controller.axis_r.when_moved = jh.right_axis_moved

        signal.pause()
except KeyboardInterrupt:
    pass
