import numpy as np
from packaging import version


class Tilt:
    @staticmethod
    def _tilt_angle_from_debug_flags(flags: int) -> int:
        """Helper function for decoding tilt angle from debug flags

        The tilt angle is encoded as an int8, with 0 at 0 degrees, and each increment representing
        0.5 degrees in either direction. A positive angle is upwards, and negative is downwards.
        """

        tilt_angle_array = np.array(
            np.right_shift(np.bitwise_and(flags, 0x0000FF0000000000), 40),
            dtype=[("tilt_angle", np.int8)],
        ).astype([("tilt_angle", np.float)])
        return tilt_angle_array["tilt_angle"] / 2

    def __init__(self, parent_drone):
        self._parent_drone = parent_drone

    def set_speed(self, speed: int):
        """Set the speed and direction of the camera tilt

        *Arguments*:

        * speed (int): Speed and direction of the tilt. 1 is max speed up, -1 is max speed down.

        Requires a drone with the tilt feature, and software version 1.5 or newer.
        A RuntimeError is raised if either of those requirements are not met.
        """
        if "tilt" not in self._parent_drone.features:
            raise RuntimeError("The connected drone does not support tilting the camera.")
        if version.parse(self._parent_drone.software_version_short) < version.parse("1.5"):
            raise RuntimeError("Drone software version is too old. Requires version 1.5 or higher.")

        # The tilt command is grouped together with the thruster commands, so to avoid messing with
        # the thruster setpoint while tilting we need to get the current setpoint and send it with
        # the tilt command.
        with self._parent_drone.motion.thruster_lock:
            thruster_setpoints = self._parent_drone.motion.current_thruster_setpoints.values()
            self._parent_drone._tcp_client.motion_input_tilt(*thruster_setpoints, 0, 0, speed)

    @property
    def angle(self) -> int:
        """Return the current angle of the camera tilt

        Requires a drone with the tilt feature, and software version 1.5 or newer.
        A RuntimeError is raised if either of those requirements are not met.
        """

        if "tilt" not in self._parent_drone.features:
            raise RuntimeError("The connected drone does not support tilting the camera.")
        if version.parse(self._parent_drone.software_version_short) < version.parse("1.5"):
            raise RuntimeError("Drone software version is too old. Requires version 1.5 or higher.")

        debug_flags = self._parent_drone._state_watcher.general_state["debug_flags"]
        return self._tilt_angle_from_debug_flags(debug_flags)


class Camera:
    def __init__(self, parent_drone):
        self._state_watcher = parent_drone._state_watcher
        self._parent_drone = parent_drone
        self.tilt = Tilt(parent_drone)

    @property
    def is_recording(self) -> bool:
        """Start or stop a camera recording

        *Arguments*:

        * is_recording (bool): Set to True to start a recording, set to False to stop the current recording

        *Returns*:

        * is_recording (bool): True if the camera is currently recording, False if not
        """
        state = self._state_watcher.general_state
        if state["camera_record_time"] != -1:
            return True
        else:
            return False

    @is_recording.setter
    def is_recording(self, start_recording: bool):
        if start_recording:
            self._parent_drone._tcp_client.start_recording()
        else:
            self._parent_drone._tcp_client.stop_recording()

    @property
    def bitrate(self) -> int:
        """Set or get the camera bitrate

        *Arguments*:

        * bitrate (int): Set the camera bitrate in bits, Valid values are in range <1 000 000, 16 000 000>

        *Returns*:

        * bitrate (int): Get the camera bitrate
        """
        camera_parameters = self._parent_drone._tcp_client.get_camera_parameters()
        bitrate = camera_parameters[1]
        return bitrate

    @bitrate.setter
    def bitrate(self, bitrate: int):
        self._parent_drone._tcp_client.set_camera_bitrate(bitrate)

    @property
    def exposure(self) -> int:
        """Set or get the camera exposure

        *Arguments*:

        * exposure (int): Set the camera exposure_value: 1 = 1/1000th of a second, 5 = 1/200th of a second. Valid values are in the range <1, 5000>

        *Returns*:

        * exposure (int): Get the camera exposure
        """
        camera_parameters = self._parent_drone._tcp_client.get_camera_parameters()
        exposure = camera_parameters[2]
        return exposure

    @exposure.setter
    def exposure(self, exposure: int):
        self._parent_drone._tcp_client.set_camera_exposure(exposure)

    @property
    def whitebalance(self) -> int:
        """Set or get the camera white balance

        *Arguments*:

        * whitebalance (int): Set the camera white balance. Valid values are in the range <2800, 9300>

        *Returns*:

        * whitebalance (int): Get the camera white balance
        """
        camera_parameters = self._parent_drone._tcp_client.get_camera_parameters()
        whitebalance = camera_parameters[3]
        return whitebalance

    @whitebalance.setter
    def whitebalance(self, whitebalance: int):
        self._parent_drone._tcp_client.set_camera_whitebalance(whitebalance)

    @property
    def hue(self) -> int:
        """Set or get the camera hue

        *Arguments*:

        * hue (int): Set the camera hue. Valid values are in the range <-40, 40>

        *Returns*:

        * hue (int): Get the camera hue
        """
        camera_parameters = self._parent_drone._tcp_client.get_camera_parameters()
        hue = camera_parameters[4]
        return hue

    @hue.setter
    def hue(self, hue: int):
        self._parent_drone._tcp_client.set_camera_hue(hue)

    @property
    def resolution(self) -> int:
        """Set or get the camera resolution

        *Arguments*:

        * resolution (int): Set the camera in vertical pixels. Valid values are 480, 720 or 1080

        *Returns*:

        * resolution (int): Get the camera resolution
        """
        camera_parameters = self._parent_drone._tcp_client.get_camera_parameters()
        resolution = camera_parameters[5]
        return resolution

    @resolution.setter
    def resolution(self, resolution: int):
        self._parent_drone._tcp_client.set_camera_resolution(resolution)

    @property
    def framerate(self) -> int:
        """Set or get the camera frame rate

        *Arguments*:

        * framerate (int): Set the camera frame rate in frames per second. Valid values are 25 or 30

        *Returns*:

        * framerate (int): Get the camera frame rate
        """
        camera_parameters = self._parent_drone._tcp_client.get_camera_parameters()
        framerate = camera_parameters[6]
        return framerate

    @framerate.setter
    def framerate(self, framerate: int):
        self._parent_drone._tcp_client.set_camera_framerate(framerate)

    @property
    def record_time(self) -> int:
        """Set or get the duration of the current camera recording

        *Returns*:

        * record_time (int): The length in seconds of the current recording, -1 if the camera is not currently recording
        """
        return self._state_watcher.general_state["camera_record_time"]

    def take_picture(self):
        """Takes a still picture and stores it locally on the drone

        These pictures can be downloaded with the Blueye App, or by any WebDAV compatible client.
        This feature was added with drone version 1.4.7, so if you try to use it with an older
        version this method will raise a RunTimeError.
        """
        if version.parse(self._parent_drone.software_version_short) >= version.parse("1.4.7"):
            self._parent_drone._tcp_client.take_still_picture()
        else:
            raise RuntimeError(
                "Drone software version is too old. Requires version 1.4.7 or higher."
            )
