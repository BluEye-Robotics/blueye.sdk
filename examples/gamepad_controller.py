import os
import threading
import time

import inputs
from blueye.sdk import Pioneer


class JoystickHandler:
    """Maps pioneer functions to joystick events"""

    def __init__(self, pioneer):
        self.pioneer = pioneer
        self.eventToFunctionMap = {
            "BTN_NORTH": self.handleXButton,
            "BTN_WEST": self.handleYButton,
            "BTN_EAST": self.handleBButton,
            "BTN_SOUTH": self.handleAButton,
            "ABS_X": self.handleLeftXAxis,
            "ABS_Y": self.handleLeftYAxis,
            "ABS_RX": self.handleRightXAxis,
            "ABS_RY": self.handleRightYAxis,
        }

    def handleXButton(self, value):
        """Starts/stops the video recording"""
        self.pioneer.camera.is_recording = value

    def handleYButton(self, value):
        """Turns lights on or off"""
        if value:
            if self.pioneer.lights > 0:
                self.pioneer.lights = 0
            else:
                self.pioneer.lights = 10

    def handleBButton(self, value):
        """Toggles autoheading"""
        if value:
            self.pioneer.motion.auto_heading_active = (
                not self.pioneer.motion.auto_heading_active
            )

    def handleAButton(self, value):
        """Toggles autodepth"""
        if value:
            self.pioneer.motion.auto_depth_active = (
                not self.pioneer.motion.auto_depth_active
            )

    def filterAndNormalize(self, value, lower=5000, upper=32768):
        """Normalizing the joystick axis range from (default) -32768<->32678 to -1<->1

        The sticks also tend to not stop at 0 when you let them go but rather some
        low value, so we'll filter those out as well.
        """
        if -lower < value < lower:
            return 0
        elif lower < value < upper:
            return (value - lower) / (upper - lower)
        elif -upper < value < -lower:
            return (value + lower) / (upper - lower)
        else:
            return 0

    def handleLeftXAxis(self, value):
        self.pioneer.motion.yaw = self.filterAndNormalize(value)

    def handleLeftYAxis(self, value):
        self.pioneer.motion.heave = self.filterAndNormalize(value)

    def handleRightXAxis(self, value):
        self.pioneer.motion.sway = self.filterAndNormalize(value)

    def handleRightYAxis(self, value):
        self.pioneer.motion.surge = -self.filterAndNormalize(value)


if __name__ == "__main__":
    try:
        p = Pioneer()
        handler = JoystickHandler(p)
        while True:
            events = inputs.get_gamepad()
            for event in events:
                if event.code in handler.eventToFunctionMap:
                    handler.eventToFunctionMap[event.code](event.state)

    except KeyboardInterrupt:
        pass
