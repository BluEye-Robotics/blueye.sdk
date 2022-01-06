from __future__ import annotations

import re
import warnings
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np
import requests

# Necessary to avoid cyclic imports
if TYPE_CHECKING:
    from .drone import Drone


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
        ).astype([("tilt_angle", float)])
        return tilt_angle_array["tilt_angle"] / 2

    def __init__(self, parent_drone: Drone):
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
        self._parent_drone._verify_required_blunux_version("1.5")

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
        self._parent_drone._verify_required_blunux_version("1.5")

        debug_flags = self._parent_drone._state_watcher.general_state["debug_flags"]
        return self._tilt_angle_from_debug_flags(debug_flags)


class LogoOverlay(Enum):
    DISABLED = 0
    BLUEYE = 1
    CUSTOM = 2


class DepthUnitOverlay(Enum):
    METERS = 0
    FEET = 1


class TemperatureUnitOverlay(Enum):
    CELSIUS = 0
    FAHRENHEIT = 1


class FontSizeOverlay(Enum):
    PX15 = 15
    PX20 = 20
    PX25 = 25
    PX30 = 30
    PX35 = 35
    PX40 = 40


class Overlay:
    """Control the overlay on videos and pictures"""

    def __init__(self, parent_drone: Drone):
        self._parent_drone = parent_drone

    @property
    def temperature_enabled(self) -> bool:
        params = self._parent_drone._tcp_client.get_overlay_parameters()
        if params[1] == 1:
            return True
        else:
            return False

    @temperature_enabled.setter
    def temperature_enabled(self, enable_temperature: bool):
        if enable_temperature is True:
            self._parent_drone._tcp_client.set_overlay_temperature_enabled(1)
        else:
            self._parent_drone._tcp_client.set_overlay_temperature_enabled(0)

    @property
    def depth_enabled(self) -> bool:
        params = self._parent_drone._tcp_client.get_overlay_parameters()
        if params[2] == 1:
            return True
        else:
            return False

    @depth_enabled.setter
    def depth_enabled(self, enable_depth: bool):
        if enable_depth is True:
            self._parent_drone._tcp_client.set_overlay_depth_enabled(1)
        else:
            self._parent_drone._tcp_client.set_overlay_depth_enabled(0)

    @property
    def heading_enabled(self) -> bool:
        params = self._parent_drone._tcp_client.get_overlay_parameters()
        if params[3] == 1:
            return True
        else:
            return False

    @heading_enabled.setter
    def heading_enabled(self, enable_heading: bool):
        if enable_heading is True:
            self._parent_drone._tcp_client.set_overlay_heading_enabled(1)
        else:
            self._parent_drone._tcp_client.set_overlay_heading_enabled(0)

    @property
    def tilt_enabled(self) -> bool:
        params = self._parent_drone._tcp_client.get_overlay_parameters()
        if params[4] == 1:
            return True
        else:
            return False

    @tilt_enabled.setter
    def tilt_enabled(self, enable_tilt: bool):
        if enable_tilt is True:
            self._parent_drone._tcp_client.set_overlay_tilt_enabled(1)
        else:
            self._parent_drone._tcp_client.set_overlay_tilt_enabled(0)

    @property
    def date_enabled(self) -> bool:
        params = self._parent_drone._tcp_client.get_overlay_parameters()
        if params[5] == 1:
            return True
        else:
            return False

    @date_enabled.setter
    def date_enabled(self, enable_date: bool):
        if enable_date is True:
            self._parent_drone._tcp_client.set_overlay_date_enabled(1)
        else:
            self._parent_drone._tcp_client.set_overlay_date_enabled(0)

    @property
    def logo(self) -> LogoOverlay:
        self._parent_drone._verify_required_blunux_version("1.8.72")
        params = self._parent_drone._tcp_client.get_overlay_parameters()
        return LogoOverlay(params[6])

    @logo.setter
    def logo(self, logo_index: LogoOverlay):
        self._parent_drone._verify_required_blunux_version("1.8.72")
        if not isinstance(logo_index, LogoOverlay):
            warnings.warn("Invalid logo index, ignoring", RuntimeWarning)
        elif logo_index.value not in range(3):
            warnings.warn("Logo index out of range, ignoring", RuntimeWarning)
        else:
            self._parent_drone._tcp_client.set_overlay_logo_index(logo_index.value)

    @property
    def depth_unit(self) -> DepthUnitOverlay:
        params = self._parent_drone._tcp_client.get_overlay_parameters()
        return DepthUnitOverlay(params[7])

    @depth_unit.setter
    def depth_unit(self, unit_index: DepthUnitOverlay):
        if not isinstance(unit_index, DepthUnitOverlay):
            warnings.warn("Invalid depth unit index, ignoring", RuntimeWarning)
        elif unit_index.value not in range(2):
            warnings.warn("Depth unit index out of range, ignoring", RuntimeWarning)
        else:
            self._parent_drone._tcp_client.set_overlay_depth_unit(unit_index.value)

    @property
    def temperature_unit(self) -> DepthUnitOverlay:
        params = self._parent_drone._tcp_client.get_overlay_parameters()
        return TemperatureUnitOverlay(params[8])

    @temperature_unit.setter
    def temperature_unit(self, unit_index: TemperatureUnitOverlay):
        if not isinstance(unit_index, TemperatureUnitOverlay):
            warnings.warn("Invalid temperature unit index, ignoring", RuntimeWarning)
        elif unit_index.value not in range(2):
            warnings.warn("Temperature unit index out of range, ignoring", RuntimeWarning)
        else:
            self._parent_drone._tcp_client.set_overlay_temperature_unit(unit_index.value)

    @property
    def timezone_offset(self) -> int:
        params = self._parent_drone._tcp_client.get_overlay_parameters()
        return params[9]

    @timezone_offset.setter
    def timezone_offset(self, offset: int):
        self._parent_drone._tcp_client.set_overlay_tz_offset(offset)

    @property
    def margin_width(self) -> int:
        params = self._parent_drone._tcp_client.get_overlay_parameters()
        return params[10]

    @margin_width.setter
    def margin_width(self, width: int):
        if width < 0:
            warnings.warn("Invalid margin width, ignoring", RuntimeWarning)
        else:
            self._parent_drone._tcp_client.set_overlay_margin_width(width)

    @property
    def margin_height(self) -> int:
        params = self._parent_drone._tcp_client.get_overlay_parameters()
        return params[11]

    @margin_height.setter
    def margin_height(self, height: int):
        if height < 0:
            warnings.warn("Invalid margin height, ignoring", RuntimeWarning)
        else:
            self._parent_drone._tcp_client.set_overlay_margin_height(height)

    @property
    def font_size(self) -> FontSizeOverlay:
        params = self._parent_drone._tcp_client.get_overlay_parameters()
        return FontSizeOverlay(params[12])

    @font_size.setter
    def font_size(self, size: FontSizeOverlay):
        if not isinstance(size, FontSizeOverlay):
            warnings.warn("Invalid font size, ignoring", RuntimeWarning)
        elif size.value not in range(15, 41):
            warnings.warn("Font size out of range, ignoring", RuntimeWarning)
        else:
            self._parent_drone._tcp_client.set_overlay_font_size(size.value)

    @property
    def title(self) -> str:
        params = self._parent_drone._tcp_client.get_overlay_parameters()
        return params[13].decode("utf-8").rstrip("\x00")

    @title.setter
    def title(self, input_title: str):
        new_title = input_title
        if len(input_title) > 63:
            warnings.warn("Too long title, truncating to 63 characters", RuntimeWarning)
            new_title = new_title[:63]
        try:
            encoded_title = bytes(new_title, "ascii")
        except UnicodeEncodeError:
            warnings.warn("Title can only contain ASCII characters, ignoring", RuntimeWarning)
            return
        self._parent_drone._tcp_client.set_overlay_title(encoded_title + b"\x00")

    @property
    def subtitle(self) -> str:
        params = self._parent_drone._tcp_client.get_overlay_parameters()
        return params[14].decode("utf-8").rstrip("\x00")

    @subtitle.setter
    def subtitle(self, input_subtitle: str):
        new_subtitle = input_subtitle
        if len(input_subtitle) > 63:
            warnings.warn("Too long subtitle, truncating to 63 characters", RuntimeWarning)
            new_subtitle = new_subtitle[:63]
        try:
            encoded_subtitle = bytes(new_subtitle, "ascii")
        except UnicodeEncodeError:
            warnings.warn("Subtitle can only contain ASCII characters, ignoring", RuntimeWarning)
            return
        self._parent_drone._tcp_client.set_overlay_subtitle(encoded_subtitle + b"\x00")

    @property
    def date_format(self) -> str:
        """Get or set the format string for the time displayed in the overlay

        Must be a string containing only ASCII characters, with a max length of 63 characters.

        The format codes are defined by the C89 standard, see
        https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
        for an overview of the available codes.
        """

        params = self._parent_drone._tcp_client.get_overlay_parameters()
        return params[15].decode("utf-8").rstrip("\x00")

    @date_format.setter
    def date_format(self, input_format_str: str):
        format_str = input_format_str
        if len(format_str) > 63:
            warnings.warn(
                "Too long date format string, truncating to 63 characters", RuntimeWarning
            )
            format_str = format_str[:63]
        try:
            encoded_format_str = bytes(format_str, "ascii")
        except UnicodeEncodeError:
            warnings.warn(
                "Date format string can only contain ASCII characters, ignoring", RuntimeWarning
            )
            return
        self._parent_drone._tcp_client.set_overlay_date_format(encoded_format_str + b"\x00")

    def upload_logo(self, path_to_logo: str):
        """Upload user selectable logo for watermarking videos and pictures

        Set the logo-property to `LogoOverlay.CUSTOM` to enable this logo.

        Allowed filetype: JPG or PNG.
        Max resolution: 2000 px.
        Max file size: 5 MB.

        Requires Blunux version 1.8.72 or newer.

        *Exceptions*:

        * `requests.exceptions.HTTPError` : Status code 400 for invalid files

        * `requests.exceptions.ConnectTimeout` : If unable to create a connection within 1s
        """
        self._parent_drone._verify_required_blunux_version("1.8.72")
        with open(path_to_logo, "rb") as f:
            url = f"http://{self._parent_drone._ip}/asset/logo"
            files = {"image": f}
            response = requests.post(url, files=files, timeout=1)
        response.raise_for_status()

    def download_logo(self, output_directory="."):
        """Download the original user uploaded logo (PNG or JPG)

        Select the download directory with the output_directory parameter.

        *Exceptions*:

        * `requests.exceptions.HTTPError` : If no custom logo is uploaded.

        * `requests.exceptions.ConnectTimeout` : If unable to create a connection within 1s
        """
        self._parent_drone._verify_required_blunux_version("1.8.72")
        response = requests.get(f"http://{self._parent_drone._ip}/asset/logo", timeout=1)
        response.raise_for_status()
        filename = re.findall('filename="(.+)"', response.headers["Content-Disposition"])[0]
        with open(f"{output_directory}/{filename}", "wb") as f:
            f.write(response.content)

    def delete_logo(self):
        """Delete the user uploaded logo from the drone

        *Exceptions*:

        * `requests.exceptions.HTTPError` : If an error occurs during deletion

        * `requests.exceptions.ConnectTimeout` : If unable to create a connection within 1s
        """
        self._parent_drone._verify_required_blunux_version("1.8.72")
        response = requests.delete(f"http://{self._parent_drone._ip}/asset/logo", timeout=1)
        response.raise_for_status()


class Camera:
    def __init__(self, parent_drone: Drone):
        self._state_watcher = parent_drone._state_watcher
        self._parent_drone = parent_drone
        self.tilt = Tilt(parent_drone)
        self.overlay = Overlay(parent_drone)

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
        self._parent_drone._verify_required_blunux_version("1.4.7")
        self._parent_drone._tcp_client.take_still_picture()
