from __future__ import annotations

import re
import warnings
from collections import namedtuple
from enum import Enum
from typing import TYPE_CHECKING, NamedTuple

import blueye.protocol
import requests

# Necessary to avoid cyclic imports
if TYPE_CHECKING:
    from .drone import Drone


class Tilt:
    def __init__(self, parent_drone: Drone):
        self._parent_drone = parent_drone

    def _verify_tilt_in_features(self):
        """Checks that the connected drone has the tilt feature

        Raises a RuntimeError if it does not.
        """
        if "tilt" not in self._parent_drone.features:
            raise RuntimeError("The connected drone does not support tilting the camera.")

    def set_velocity(self, velocity: float):
        """Set the speed and direction of the camera tilt

        *Arguments*:

        * velocity (float): Speed and direction of the tilt. 1 is max speed up, -1 is max speed down.

        Raises a RuntimeError if the connected drone does not have the tilt option
        """
        self._verify_tilt_in_features()
        self._parent_drone._ctrl_client.set_tilt_velocity(velocity)

    @property
    def angle(self) -> float:
        """Return the current angle of the camera tilt

        Raises a RuntimeError if the connected drone does not have the tilt option
        """
        self._verify_tilt_in_features()
        TiltAngleTel = self._parent_drone._telemetry_watcher.state["blueye.protocol.TiltAngleTel"]
        tilt_angle = blueye.protocol.TiltAngleTel.deserialize(TiltAngleTel).angle.value
        return tilt_angle

    @property
    def stabilization_enabled(self) -> bool:
        """Get or set the state of active camera stabilization

        *Arguments*:

        * enabled (bool): True to turn stabilization on, False to turn it off

        *Returns*:

        * enabled (bool): Current state of active camera stabilization
        """
        self._verify_tilt_in_features()
        TiltStabilizationTel = self._parent_drone._telemetry_watcher.state[
            "blueye.protocol.TiltStabilizationTel"
        ]
        tilt_stabilization = blueye.protocol.TiltStabilizationTel.deserialize(
            TiltStabilizationTel
        ).state.enabled
        return tilt_stabilization

    @stabilization_enabled.setter
    def stabilization_enabled(self, enabled: bool):
        self._verify_tilt_in_features()
        self._parent_drone._ctrl_client.set_tilt_stabilization(enabled)


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

    def _get_named_overlay_parameters(self) -> NamedTuple:
        """Get overlay parameters from drone and convert them to a named tuple"""

        NamedParameters = namedtuple(
            "Parameters",
            [
                "returned_parameter",
                "temperature_enabled",
                "depth_enabled",
                "heading_enabled",
                "tilt_enabled",
                "date_enabled",
                "logo_index",
                "depth_unit",
                "temperature_unit",
                "tz_offset",
                "margin_width",
                "margin_height",
                "font_size",
                "title",
                "subtitle",
                "date_format",
            ],
        )
        parameters = self._parent_drone._tcp_client.get_overlay_parameters()
        return NamedParameters(*parameters)

    @property
    def temperature_enabled(self) -> bool:
        """Get or set the state of the temperature overlay

        Requires Blunux version 1.7.60 or newer.
        """

        self._parent_drone._verify_required_blunux_version("1.7.60")
        return bool(self._get_named_overlay_parameters().temperature_enabled)

    @temperature_enabled.setter
    def temperature_enabled(self, enable_temperature: bool):
        self._parent_drone._verify_required_blunux_version("1.7.60")
        self._parent_drone._tcp_client.set_overlay_temperature_enabled(
            1 if enable_temperature else 0
        )

    @property
    def depth_enabled(self) -> bool:
        """Get or set the state of the depth overlay

        Requires Blunux version 1.7.60 or newer.
        """

        self._parent_drone._verify_required_blunux_version("1.7.60")
        return bool(self._get_named_overlay_parameters().depth_enabled)

    @depth_enabled.setter
    def depth_enabled(self, enable_depth: bool):
        self._parent_drone._verify_required_blunux_version("1.7.60")
        self._parent_drone._tcp_client.set_overlay_depth_enabled(1 if enable_depth else 0)

    @property
    def heading_enabled(self) -> bool:
        """Get or set the state of the heading overlay

        Requires Blunux version 1.7.60 or newer.
        """

        self._parent_drone._verify_required_blunux_version("1.7.60")
        return bool(self._get_named_overlay_parameters().heading_enabled)

    @heading_enabled.setter
    def heading_enabled(self, enable_heading: bool):
        self._parent_drone._verify_required_blunux_version("1.7.60")
        self._parent_drone._tcp_client.set_overlay_heading_enabled(1 if enable_heading else 0)

    @property
    def tilt_enabled(self) -> bool:
        """Get or set the state of the tilt overlay

        Requires Blunux version 1.7.60 or newer.
        """

        self._parent_drone._verify_required_blunux_version("1.7.60")
        return bool(self._get_named_overlay_parameters().tilt_enabled)

    @tilt_enabled.setter
    def tilt_enabled(self, enable_tilt: bool):
        self._parent_drone._verify_required_blunux_version("1.7.60")
        self._parent_drone._tcp_client.set_overlay_tilt_enabled(1 if enable_tilt else 0)

    @property
    def date_enabled(self) -> bool:
        """Get or set the state of the date overlay

        Requires Blunux version 1.7.60 or newer.
        """

        self._parent_drone._verify_required_blunux_version("1.7.60")
        return bool(self._get_named_overlay_parameters().date_enabled)

    @date_enabled.setter
    def date_enabled(self, enable_date: bool):
        self._parent_drone._verify_required_blunux_version("1.7.60")
        self._parent_drone._tcp_client.set_overlay_date_enabled(1 if enable_date else 0)

    @property
    def logo(self) -> LogoOverlay:
        """Get or set logo overlay selection

        Needs to be set to an instance of the `LogoOverlay` class, if not a RuntimeWarning is
        raised.

        Requires Blunux version 1.8.72 or newer.
        """

        self._parent_drone._verify_required_blunux_version("1.8.72")
        return LogoOverlay(self._get_named_overlay_parameters().logo_index)

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
        """Get or set the depth unit for the overlay

        Needs to be set to an instance of the `DepthUnitOverlay` class, if not a RuntimeWarning is
        raised.

        Requires Blunux version 1.7.60 or newer.
        """

        self._parent_drone._verify_required_blunux_version("1.7.60")
        return DepthUnitOverlay(self._get_named_overlay_parameters().depth_unit)

    @depth_unit.setter
    def depth_unit(self, unit_index: DepthUnitOverlay):
        self._parent_drone._verify_required_blunux_version("1.7.60")
        if not isinstance(unit_index, DepthUnitOverlay):
            warnings.warn("Invalid depth unit index, ignoring", RuntimeWarning)
        elif unit_index.value not in range(2):
            warnings.warn("Depth unit index out of range, ignoring", RuntimeWarning)
        else:
            self._parent_drone._tcp_client.set_overlay_depth_unit(unit_index.value)

    @property
    def temperature_unit(self) -> TemperatureUnitOverlay:
        """Get or set the temperature unit for the overlay

        Needs to be set to an instance of the `TemperatureUnitOverlay` class, if not a
        RuntimeWarning is raised.

        Requires Blunux version 1.7.60 or newer.
        """

        self._parent_drone._verify_required_blunux_version("1.7.60")
        return TemperatureUnitOverlay(self._get_named_overlay_parameters().temperature_unit)

    @temperature_unit.setter
    def temperature_unit(self, unit_index: TemperatureUnitOverlay):
        self._parent_drone._verify_required_blunux_version("1.7.60")
        if not isinstance(unit_index, TemperatureUnitOverlay):
            warnings.warn("Invalid temperature unit index, ignoring", RuntimeWarning)
        elif unit_index.value not in range(2):
            warnings.warn("Temperature unit index out of range, ignoring", RuntimeWarning)
        else:
            self._parent_drone._tcp_client.set_overlay_temperature_unit(unit_index.value)

    @property
    def timezone_offset(self) -> int:
        """Get or set the timezone offset for the overlay

        Set to the number of minutes (either positive or negative) the timestamp should be offset.

        Requires Blunux version 1.7.60 or newer.
        """

        self._parent_drone._verify_required_blunux_version("1.7.60")
        return self._get_named_overlay_parameters().tz_offset

    @timezone_offset.setter
    def timezone_offset(self, offset: int):
        self._parent_drone._verify_required_blunux_version("1.7.60")
        self._parent_drone._tcp_client.set_overlay_tz_offset(offset)

    @property
    def margin_width(self) -> int:
        """Get or set the margin width for the overlay

        The amount of pixels to use as margin on the right and left side of the overlay. Needs to
        be a positive integer.

        Requires Blunux version 1.7.60 or newer.
        """

        self._parent_drone._verify_required_blunux_version("1.7.60")
        return self._get_named_overlay_parameters().margin_width

    @margin_width.setter
    def margin_width(self, width: int):
        self._parent_drone._verify_required_blunux_version("1.7.60")
        if width < 0:
            warnings.warn("Invalid margin width, ignoring", RuntimeWarning)
        else:
            self._parent_drone._tcp_client.set_overlay_margin_width(width)

    @property
    def margin_height(self) -> int:
        """Get or set the margin height for the overlay

        The amount of pixels to use as margin on the top and bottom side of the overlay. Needs to be
        a positive integer.

        Requires Blunux version 1.7.60 or newer.
        """

        self._parent_drone._verify_required_blunux_version("1.7.60")
        return self._get_named_overlay_parameters().margin_height

    @margin_height.setter
    def margin_height(self, height: int):
        self._parent_drone._verify_required_blunux_version("1.7.60")
        if height < 0:
            warnings.warn("Invalid margin height, ignoring", RuntimeWarning)
        else:
            self._parent_drone._tcp_client.set_overlay_margin_height(height)

    @property
    def font_size(self) -> FontSizeOverlay:
        """Get or set the font size for the overlay

        Needs to be an instance of the `FontSizeOverlay` class, if not a RuntimeWarning is raised.

        Requires Blunux version 1.7.60 or newer.
        """

        self._parent_drone._verify_required_blunux_version("1.7.60")
        return FontSizeOverlay(self._get_named_overlay_parameters().font_size)

    @font_size.setter
    def font_size(self, size: FontSizeOverlay):
        self._parent_drone._verify_required_blunux_version("1.7.60")
        if not isinstance(size, FontSizeOverlay):
            warnings.warn("Invalid font size, ignoring", RuntimeWarning)
        elif size.value not in range(15, 41):
            warnings.warn("Font size out of range, ignoring", RuntimeWarning)
        else:
            self._parent_drone._tcp_client.set_overlay_font_size(size.value)

    @property
    def title(self) -> str:
        """Get or set the title for the overlay

        The title needs to be a string of only ASCII characters with a maximum length of 63
        characters. If a longer title is passed it will be truncated, and a RuntimeWarning is
        raised.

        Set to an empty string to disable title.

        Requires Blunux version 1.7.60 or newer.
        """
        self._parent_drone._verify_required_blunux_version("1.7.60")
        return self._get_named_overlay_parameters().title.decode("utf-8").rstrip("\x00")

    @title.setter
    def title(self, input_title: str):
        self._parent_drone._verify_required_blunux_version("1.7.60")
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
        """Get or set the subtitle for the overlay

        The subtitle needs to be a string of only ASCII characters with a maximum length of 63
        characters. If a longer subtitle is passed it will be truncated, and a RuntimeWarning is
        raised.

        Set to an empty string to disable the subtitle.

        Requires Blunux version 1.7.60 or newer.
        """
        self._parent_drone._verify_required_blunux_version("1.7.60")
        return self._get_named_overlay_parameters().subtitle.decode("utf-8").rstrip("\x00")

    @subtitle.setter
    def subtitle(self, input_subtitle: str):
        self._parent_drone._verify_required_blunux_version("1.7.60")
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

        self._parent_drone._verify_required_blunux_version("1.7.60")
        return self._get_named_overlay_parameters().date_format.decode("utf-8").rstrip("\x00")

    @date_format.setter
    def date_format(self, input_format_str: str):
        self._parent_drone._verify_required_blunux_version("1.7.60")
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
    def __init__(self, parent_drone: Drone, is_guestport_camera: bool = False):
        self._state_watcher = parent_drone._state_watcher
        self._parent_drone = parent_drone
        self._is_guestport_camera = is_guestport_camera
        if not self._is_guestport_camera:
            self.tilt = Tilt(parent_drone)
            self.overlay = Overlay(parent_drone)

    def _get_record_state(self) -> blueye.protocol.RecordState:
        record_state_tel = self._parent_drone._telemetry_watcher.state[
            "blueye.protocol.RecordStateTel"
        ]
        return blueye.protocol.RecordStateTel.deserialize(record_state_tel).record_state

    @property
    def is_recording(self) -> bool:
        """Get or set the camera recording state

        *Arguments*:

        * start_recording (bool): Set to True to start a recording, set to False to stop the current
                                  recording.

        *Returns*:

        * Recording state (bool): True if the camera is currently recording, False if not
        """
        record_state = self._get_record_state()
        if self._is_guestport_camera:
            return record_state.guestport_is_recording
        else:
            return record_state.main_is_recording

    @is_recording.setter
    def is_recording(self, start_recording: bool):
        record_state = self._get_record_state()
        if self._is_guestport_camera:
            self._parent_drone._ctrl_client.set_recording_state(
                record_state.main_is_recording, start_recording
            )
        else:
            self._parent_drone._ctrl_client.set_recording_state(
                start_recording, record_state.guestport_is_recording
            )

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

        * resolution (int): Set the camera in vertical pixels. Valid values are 720 or 1080

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
