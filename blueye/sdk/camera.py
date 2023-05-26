from __future__ import annotations

import re
import warnings
from typing import TYPE_CHECKING, Optional

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
    def angle(self) -> Optional[float]:
        """Return the current angle of the camera tilt

        Raises a RuntimeError if the connected drone does not have the tilt option
        """
        self._verify_tilt_in_features()
        try:
            TiltAngleTel = self._parent_drone._telemetry_watcher.get(blueye.protocol.TiltAngleTel)
        except KeyError:
            return None
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
        TiltStabilizationTel = self._parent_drone._telemetry_watcher.get(
            blueye.protocol.TiltStabilizationTel
        )
        tilt_stabilization = blueye.protocol.TiltStabilizationTel.deserialize(
            TiltStabilizationTel
        ).state.enabled
        return tilt_stabilization

    @stabilization_enabled.setter
    def stabilization_enabled(self, enabled: bool):
        self._verify_tilt_in_features()
        self._parent_drone._ctrl_client.set_tilt_stabilization(enabled)


class Overlay:
    """Control the overlay on videos and pictures"""

    def __init__(self, parent_drone: Drone):
        self._parent_drone = parent_drone
        self._overlay_parametres = None

    def _update_overlay_parameters(self):
        self._overlay_parametres = self._parent_drone._req_rep_client.get_overlay_parameters()

    @property
    def temperature_enabled(self) -> bool:
        """Get or set the state of the temperature overlay"""
        self._update_overlay_parameters()
        return self._overlay_parametres.temperature_enabled

    @temperature_enabled.setter
    def temperature_enabled(self, enable_temperature: bool):
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.temperature_enabled = enable_temperature
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    @property
    def depth_enabled(self) -> bool:
        """Get or set the state of the depth overlay"""

        self._update_overlay_parameters()
        return self._overlay_parametres.depth_enabled

    @depth_enabled.setter
    def depth_enabled(self, enable_depth: bool):
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.depth_enabled = enable_depth
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    @property
    def heading_enabled(self) -> bool:
        """Get or set the state of the heading overlay"""
        self._update_overlay_parameters()
        return self._overlay_parametres.heading_enabled

    @heading_enabled.setter
    def heading_enabled(self, enable_heading: bool):
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.heading_enabled = enable_heading
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    @property
    def tilt_enabled(self) -> bool:
        """Get or set the state of the tilt overlay"""
        self._update_overlay_parameters()
        return self._overlay_parametres.tilt_enabled

    @tilt_enabled.setter
    def tilt_enabled(self, enable_tilt: bool):
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.tilt_enabled = enable_tilt
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    @property
    def date_enabled(self) -> bool:
        """Get or set the state of the date overlay"""
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        return self._overlay_parametres.date_enabled

    @date_enabled.setter
    def date_enabled(self, enable_date: bool):
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.date_enabled = enable_date
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    @property
    def logo(self) -> blueye.protcol.LogoType:
        """Get or set logo overlay selection

        Needs to be set to an instance of the `blueye.protocol.LogoType` enum, if not a
        RuntimeWarning is raised.

        """
        self._update_overlay_parameters()
        return self._overlay_parametres.logo_type

    @logo.setter
    def logo(self, logo_type: blueye.protocol.LogoType):
        if not isinstance(logo_type, blueye.protocol.LogoType):
            warnings.warn("Invalid logo type, ignoring", RuntimeWarning)
        else:
            if self._overlay_parametres is None:
                self._update_overlay_parameters()
            self._overlay_parametres.logo_type = logo_type
            self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    @property
    def depth_unit(self) -> blueye.protocol.DepthUnit:
        """Get or set the depth unit for the overlay

        Needs to be set to an instance of the `blueye.protocol.DepthUnit` enum, if not a
        RuntimeWarning is raised.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.depth_unit

    @depth_unit.setter
    def depth_unit(self, unit: blueye.protocol.DepthUnit):
        if not isinstance(unit, blueye.protocol.DepthUnit):
            warnings.warn("Invalid depth unit, ignoring", RuntimeWarning)
        else:
            if self._overlay_parametres is None:
                self._update_overlay_parameters()
            self._overlay_parametres.depth_unit = unit
            self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    @property
    def temperature_unit(self) -> blueye.protocol.TemperatureUnit:
        """Get or set the temperature unit for the overlay

        Needs to be set to an instance of the `blueye.protocol.TemperatureUnit` enum, if not a
        RuntimeWarning is raised.
        """

        self._update_overlay_parameters()
        return self._overlay_parametres.temperature_unit

    @temperature_unit.setter
    def temperature_unit(self, unit: blueye.protocol.TemperatureUnit):
        if not isinstance(unit, blueye.protocol.TemperatureUnit):
            warnings.warn("Invalid temperature unit, ignoring", RuntimeWarning)
        else:
            if self._overlay_parametres is None:
                self._update_overlay_parameters()
            self._overlay_parametres.temperature_unit = unit
            self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    @property
    def timezone_offset(self) -> int:
        """Get or set the timezone offset for the overlay

        Set to the number of minutes (either positive or negative) the timestamp should be offset.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.timezone_offset

    @timezone_offset.setter
    def timezone_offset(self, offset: int):
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.timezone_offset = offset
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    @property
    def margin_width(self) -> int:
        """Get or set the margin width for the overlay

        The amount of pixels to use as margin on the right and left side of the overlay. Needs to
        be a positive integer.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.margin_width

    @margin_width.setter
    def margin_width(self, width: int):
        if width < 0:
            warnings.warn("Invalid margin width, ignoring", RuntimeWarning)
        else:
            if self._overlay_parametres is None:
                self._update_overlay_parameters()
            self._overlay_parametres.margin_width = width
            self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    @property
    def margin_height(self) -> int:
        """Get or set the margin height for the overlay

        The amount of pixels to use as margin on the top and bottom side of the overlay. Needs to be
        a positive integer.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.margin_height

    @margin_height.setter
    def margin_height(self, height: int):
        if height < 0:
            warnings.warn("Invalid margin height, ignoring", RuntimeWarning)
        else:
            if self._overlay_parametres is None:
                self._update_overlay_parameters()
            self._overlay_parametres.margin_height = height
            self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    @property
    def font_size(self) -> blueye.protocol.FontSize:
        """Get or set the font size for the overlay

        Needs to be an instance of the `blueye.protocol.Fontsize` enum, if not a RuntimeWarning is
        raised.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.font_size

    @font_size.setter
    def font_size(self, size: blueye.protocol.FontSize):
        if not isinstance(size, blueye.protocol.FontSize):
            warnings.warn("Invalid font size, ignoring", RuntimeWarning)
        else:
            if self._overlay_parametres is None:
                self._update_overlay_parameters()
            self._overlay_parametres.font_size = size
            self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    @property
    def title(self) -> str:
        """Get or set the title for the overlay

        The title needs to be a string of only ASCII characters with a maximum length of 63
        characters. If a longer title is passed it will be truncated, and a RuntimeWarning is
        raised.

        Set to an empty string to disable title.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.title

    @title.setter
    def title(self, input_title: str):
        new_title = input_title
        if len(input_title) > 63:
            warnings.warn("Too long title, truncating to 63 characters", RuntimeWarning)
            new_title = new_title[:63]
        try:
            bytes(new_title, "ascii")
        except UnicodeEncodeError:
            warnings.warn("Title can only contain ASCII characters, ignoring", RuntimeWarning)
            return
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.title = new_title
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    @property
    def subtitle(self) -> str:
        """Get or set the subtitle for the overlay

        The subtitle needs to be a string of only ASCII characters with a maximum length of 63
        characters. If a longer subtitle is passed it will be truncated, and a RuntimeWarning is
        raised.

        Set to an empty string to disable the subtitle.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.subtitle

    @subtitle.setter
    def subtitle(self, input_subtitle: str):
        new_subtitle = input_subtitle
        if len(input_subtitle) > 63:
            warnings.warn("Too long subtitle, truncating to 63 characters", RuntimeWarning)
            new_subtitle = new_subtitle[:63]
        try:
            bytes(new_subtitle, "ascii")
        except UnicodeEncodeError:
            warnings.warn("Subtitle can only contain ASCII characters, ignoring", RuntimeWarning)
            return
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.subtitle = new_subtitle
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    @property
    def date_format(self) -> str:
        """Get or set the format string for the time displayed in the overlay

        Must be a string containing only ASCII characters, with a max length of 63 characters.

        The format codes are defined by the C89 standard, see
        https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
        for an overview of the available codes.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.date_format

    @date_format.setter
    def date_format(self, input_format_str: str):
        format_str = input_format_str
        if len(format_str) > 63:
            warnings.warn(
                "Too long date format string, truncating to 63 characters", RuntimeWarning
            )
            format_str = format_str[:63]
        try:
            bytes(format_str, "ascii")
        except UnicodeEncodeError:
            warnings.warn(
                "Date format string can only contain ASCII characters, ignoring", RuntimeWarning
            )
            return
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.date_format = format_str
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    def upload_logo(self, path_to_logo: str, timeout: float = 1.0):
        """Upload user selectable logo for watermarking videos and pictures

        Set the logo-property to `blueye.protocol.LogoType.LOG_TYPE_CUSTOM` to enable this logo.

        Allowed filetype: JPG or PNG.
        Max resolution: 2000 px.
        Max file size: 5 MB.

        *Exceptions*:

        * `requests.exceptions.HTTPError` : Status code 400 for invalid files

        * `requests.exceptions.ConnectTimeout` : If unable to create a connection within specified
                                                 timeout (default 1s)
        """

        with open(path_to_logo, "rb") as f:
            url = f"http://{self._parent_drone._ip}/asset/logo"
            files = {"image": f}
            response = requests.post(url, files=files, timeout=timeout)
        response.raise_for_status()

    def download_logo(self, output_directory=".", timeout: float = 1.0):
        """Download the original user uploaded logo (PNG or JPG)

        Select the download directory with the output_directory parameter.

        *Exceptions*:

        * `requests.exceptions.HTTPError` : If no custom logo is uploaded.

        * `requests.exceptions.ConnectTimeout` : If unable to create a connection within specified
                                                 timeout (default 1s)
        """

        response = requests.get(f"http://{self._parent_drone._ip}/asset/logo", timeout=timeout)
        response.raise_for_status()
        filename = re.findall('filename="(.+)"', response.headers["Content-Disposition"])[0]
        with open(f"{output_directory}/{filename}", "wb") as f:
            f.write(response.content)

    def delete_logo(self, timeout: float = 1.0):
        """Delete the user uploaded logo from the drone

        *Exceptions*:

        * `requests.exceptions.HTTPError` : If an error occurs during deletion

        * `requests.exceptions.ConnectTimeout` : If unable to create a connection within specified
                                                 timeout (default 1s)
        """

        response = requests.delete(f"http://{self._parent_drone._ip}/asset/logo", timeout=timeout)
        response.raise_for_status()


class Camera:
    def __init__(self, parent_drone: Drone, is_guestport_camera: bool = False):
        self._parent_drone = parent_drone
        self._is_guestport_camera = is_guestport_camera
        self._camera_type = (
            blueye.protocol.Camera.CAMERA_GUESTPORT
            if is_guestport_camera
            else blueye.protocol.Camera.CAMERA_MAIN
        )
        if not self._is_guestport_camera:
            self.tilt = Tilt(parent_drone)
            self.overlay = Overlay(parent_drone)
        self._camera_parameters = None

    def _get_record_state(self) -> blueye.protocol.RecordState:
        record_state_tel = self._parent_drone._telemetry_watcher.get(blueye.protocol.RecordStateTel)
        return blueye.protocol.RecordStateTel.deserialize(record_state_tel).record_state

    def _update_camera_parameters(self):
        self._camera_parameters = self._parent_drone._req_rep_client.get_camera_parameters(
            camera=self._camera_type
        )

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
        """Set or get the video stream bitrate

        *Arguments*:

        * bitrate (int): Set the video stream bitrate in bits, valid values are in range
                         (1 000 000..16 000 000)

        *Returns*:

        * bitrate (int): The H264 video stream bitrate
        """
        self._update_camera_parameters()
        return self._camera_parameters.h264_bitrate

    @bitrate.setter
    def bitrate(self, bitrate: int):
        if self._camera_parameters is None:
            self._update_camera_parameters()
        self._camera_parameters.h264_bitrate = bitrate
        self._parent_drone._req_rep_client.set_camera_parameters(self._camera_parameters)

    @property
    def bitrate_still_picture(self) -> int:
        """Set or get the bitrate for the still picture stream

        *Arguments*:

        * bitrate (int): Set the still picture stream bitrate in bits, valid values are in range
                         (1 000 000 .. 300 000 000). Default value is 100 000 000.

        *Returns*:

        * bitrate (int): The still picture stream bitrate
        """
        self._update_camera_parameters()
        return self._camera_parameters.mjpg_bitrate

    @bitrate_still_picture.setter
    def bitrate_still_picture(self, bitrate: int):
        if self._camera_parameters is None:
            self._update_camera_parameters()
        self._camera_parameters.mjpg_bitrate = bitrate
        self._parent_drone._req_rep_client.set_camera_parameters(self._camera_parameters)

    @property
    def exposure(self) -> int:
        """Set or get the camera exposure

        *Arguments*:

        * exposure (int): Set the camera exposure time. Unit is thousandths of a second, ie.
                          5 = 5s/1000. Valid values are in the range (1 .. 5000) or -1 for auto
                          exposure

        *Returns*:

        * exposure (int): Get the camera exposure
        """
        self._update_camera_parameters()
        return self._camera_parameters.exposure

    @exposure.setter
    def exposure(self, exposure: int):
        if self._camera_parameters is None:
            self._update_camera_parameters()
        self._camera_parameters.exposure = exposure
        self._parent_drone._req_rep_client.set_camera_parameters(self._camera_parameters)

    @property
    def whitebalance(self) -> int:
        """Set or get the camera white balance

        *Arguments*:

        * white_balance (int): Set the camera white balance. Valid values are in the range
                               (2800..9300) or -1 for auto white balance

        *Returns*:

        * white_balance (int): Get the camera white balance
        """
        self._update_camera_parameters()
        return self._camera_parameters.white_balance

    @whitebalance.setter
    def whitebalance(self, white_balance: int):
        if self._camera_parameters is None:
            self._update_camera_parameters()
        self._camera_parameters.white_balance = white_balance
        self._parent_drone._req_rep_client.set_camera_parameters(self._camera_parameters)

    @property
    def hue(self) -> int:
        """Set or get the camera hue

        *Arguments*:

        * hue (int): Set the camera hue. Valid values are in the range (-40..40)

        *Returns*:

        * hue (int): Get the camera hue
        """
        self._update_camera_parameters()
        return self._camera_parameters.hue

    @hue.setter
    def hue(self, hue: int):
        if self._camera_parameters is None:
            self._update_camera_parameters()
        self._camera_parameters.hue = hue
        self._parent_drone._req_rep_client.set_camera_parameters(self._camera_parameters)

    @property
    def resolution(self) -> int:
        """Set or get the camera resolution

        *Arguments*:

        * resolution (int): Set the camera in vertical pixels. Valid values are 720 or 1080

        *Returns*:

        * resolution (int): Get the camera resolution
        """
        self._update_camera_parameters()
        if self._camera_parameters.resolution == blueye.protocol.Resolution.RESOLUTION_HD_720P:
            return 720
        elif (
            self._camera_parameters.resolution == blueye.protocol.Resolution.RESOLUTION_FULLHD_1080P
        ):
            return 1080

    @resolution.setter
    def resolution(self, resolution: int):
        if resolution not in (720, 1080):
            raise ValueError(
                f"{resolution} is not a valid resolution. Valid values are 720 or 1080"
            )
        if self._camera_parameters is None:
            self._update_camera_parameters()
        if resolution == 720:
            self._camera_parameters.resolution = blueye.protocol.Resolution.RESOLUTION_HD_720P
        elif resolution == 1080:
            self._camera_parameters.resolution = blueye.protocol.Resolution.RESOLUTION_FULLHD_1080P

        self._parent_drone._req_rep_client.set_camera_parameters(self._camera_parameters)

    @property
    def framerate(self) -> int:
        """Set or get the camera frame rate

        *Arguments*:

        * framerate (int): Set the camera frame rate in frames per second. Valid values are 25 or 30

        *Returns*:

        * framerate (int): Get the camera frame rate
        """
        self._update_camera_parameters()
        if self._camera_parameters.framerate == blueye.protocol.Framerate.FRAMERATE_FPS_25:
            return 25
        elif self._camera_parameters.framerate == blueye.protocol.Framerate.FRAMERATE_FPS_30:
            return 30

    @framerate.setter
    def framerate(self, framerate: int):
        if framerate not in (25, 30):
            raise ValueError(f"{framerate} is not a valid framerate. Valid values are 25 or 30")
        if self._camera_parameters is None:
            self._update_camera_parameters()
        if framerate == 25:
            self._camera_parameters.framerate = blueye.protocol.Framerate.FRAMERATE_FPS_25
        elif framerate == 30:
            self._camera_parameters.framerate = blueye.protocol.Framerate.FRAMERATE_FPS_30
        self._parent_drone._req_rep_client.set_camera_parameters(self._camera_parameters)

    @property
    def record_time(self) -> int:
        """Set or get the duration of the current camera recording

        *Returns*:

        * record_time (int): The length in seconds of the current recording, -1 if the camera is not currently recording
        """
        record_state = self._get_record_state()
        if self._is_guestport_camera:
            return record_state.guestport_seconds
        else:
            return record_state.main_seconds

    def take_picture(self):
        """Takes a still picture and stores it locally on the drone

        These pictures can be downloaded with the Blueye App, or by any WebDAV compatible client.
        """
        self._parent_drone._ctrl_client.take_still_picture()
