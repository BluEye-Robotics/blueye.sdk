from __future__ import annotations

import logging
import re
import warnings
from typing import TYPE_CHECKING, Optional

import blueye.protocol
import requests

# Necessary to avoid cyclic imports
if TYPE_CHECKING:
    from .drone import Drone


logger = logging.getLogger(__name__)


class Tilt:
    """Handles the camera tilt functionality for the Blueye drone."""

    def __init__(self, parent_drone: Drone):
        """Initialize the Tilt class.

        Args:
            parent_drone (Drone): The parent drone instance.
        """
        self._parent_drone = parent_drone

    def _verify_tilt_in_features(self):
        """Check that the connected drone has the tilt feature.

        Raises:
            RuntimeError: If the connected drone does not support tilting the camera.
        """
        if "tilt" not in self._parent_drone.features:
            raise RuntimeError("The connected drone does not support tilting the camera.")

    def set_velocity(self, velocity: float):
        """Set the speed and direction of the camera tilt.

        Args:
            velocity: Speed and direction of the tilt. 1 is max speed up, -1 is max speed down.

        Raises:
            RuntimeError: If the connected drone does not have the tilt option.
        """
        self._verify_tilt_in_features()
        self._parent_drone._ctrl_client.set_tilt_velocity(velocity)

    @property
    def angle(self) -> Optional[float]:
        """Return the current angle of the camera tilt.

        Returns:
            The current angle of the camera tilt.

        Raises:
            RuntimeError: If the connected drone does not have the tilt option.
        """
        self._verify_tilt_in_features()
        tilt_angle_tel = self._parent_drone.telemetry.get(blueye.protocol.TiltAngleTel)
        if tilt_angle_tel is not None:
            return tilt_angle_tel.angle.value
        else:
            return None

    @property
    def stabilization_enabled(self) -> Optional[bool]:
        """Get the state of active camera stabilization.

        Returns:
            The current state of active camera stabilization.

        Raises:
            RuntimeError: If the connected drone does not have the tilt option.
        """
        self._verify_tilt_in_features()
        tilt_stab_tel = self._parent_drone.telemetry.get(blueye.protocol.TiltStabilizationTel)
        if tilt_stab_tel is not None:
            return tilt_stab_tel.state.enabled
        else:
            return None

    @stabilization_enabled.setter
    def stabilization_enabled(self, enabled: bool):
        """Set the state of active camera stabilization.

        Args:
            enabled (bool): True to turn stabilization on, False to turn it off.

        Raises:
            RuntimeError: If the connected drone does not have the tilt option.
        """
        self._verify_tilt_in_features()
        self._parent_drone._ctrl_client.set_tilt_stabilization(enabled)


class Overlay:
    """Control the overlay on videos and pictures."""

    def __init__(self, parent_drone: Drone):
        """Initialize the Overlay class.

        Args:
            parent_drone (Drone): The parent drone instance.
        """
        self._parent_drone = parent_drone
        self._overlay_parametres = None

    def _update_overlay_parameters(self):
        """Update the overlay parameters from the drone."""
        self._overlay_parametres = self._parent_drone._req_rep_client.get_overlay_parameters()

    @property
    def temperature_enabled(self) -> bool:
        """Get or set the state of the temperature overlay.

        Returns:
            The current state of the temperature overlay.

        Args:
            enable_temperature (bool): True to enable the temperature overlay, False to disable it.
        """
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
        """Get or set the state of the depth overlay.

        Returns:
            The current state of the depth overlay.

        Args:
            enable_depth (bool): True to enable the depth overlay, False to disable it.
        """
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
        """Get or set the state of the heading overlay.

        Returns:
            The current state of the heading overlay.

        Args:
            enable_heading (bool): True to enable the heading overlay, False to disable it.
        """
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
        """Get or set the state of the tilt overlay.

        Returns:
            The current state of the tilt overlay.

        Args:
            enable_tilt (bool): True to enable the tilt overlay, False to disable it.
        """
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
        """Get or set the state of the date overlay.

        Returns:
            The current state of the date overlay.

        Args:
            enable_date (bool): True to enable the date overlay, False to disable it.
        """
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
    def logo(self) -> blueye.protocol.LogoType:
        """Get or set logo overlay selection.

        Returns:
            The current logo type.

        Args:
            logo_type (blueye.protocol.LogoType): The logo type.

        Warns:
            RuntimeWarning: If the logo type is not an instance of blueye.protocol.LogoType.
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
        """Get or set the depth unit for the overlay.

        Returns:
            The current depth unit.

        Args:
            unit (blueye.protocol.DepthUnit): The depth unit to set.

        Warns:
            RuntimeWarning: If the unit is not an instance of blueye.protocol.DepthUnit.
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
        """Get or set the temperature unit for the overlay.

        Returns:
            The current temperature unit.

        Args:
            unit (blueye.protocol.TemperatureUnit): The temperature unit to set.

        Warns:
            RuntimeWarning: If the unit is not an instance of blueye.protocol.TemperatureUnit.
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
    def cp_probe_enabled(self) -> bool:
        """Get or set the state of the CP probe overlay.

        Returns:
            The current state of the CP probe overlay.

        Args:
            enable_cp_probe (bool): True to enable the CP probe overlay, False to disable it.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.cp_probe_enabled

    @cp_probe_enabled.setter
    def cp_probe_enabled(self, enable_cp_probe: bool):
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.cp_probe_enabled = enable_cp_probe
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    @property
    def distance_enabled(self) -> bool:
        """Get or set the state of the distance overlay.

        Returns:
            The current state of the distance overlay.

        Args:
            enable_distance (bool): True to enable the distance overlay, False to disable it.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.distance_enabled

    @distance_enabled.setter
    def distance_enabled(self, enable_distance: bool):
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.distance_enabled = enable_distance
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    @property
    def altitude_enabled(self) -> bool:
        """Get or set the state of the altitude overlay.

        Returns:
            The current state of the altitude overlay.

        Args:
            enable_altitude (bool): True to enable the altitude overlay, False to disable it.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.altitude_enabled

    @altitude_enabled.setter
    def altitude_enabled(self, enable_altitude: bool):
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.altitude_enabled = enable_altitude
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    @property
    def thickness_enabled(self) -> bool:
        """Get or set the state of the thickness overlay.

        Returns:
            The current state of the thickness overlay.

        Args:
            enable_thickness (bool): True to enable the thickness overlay, False to disable it.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.thickness_enabled

    @thickness_enabled.setter
    def thickness_enabled(self, enable_thickness: bool):
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.thickness_enabled = enable_thickness
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    @property
    def thickness_unit(self) -> blueye.protocol.ThicknessUnit:
        """Get or set the thickness unit for the overlay.

        Returns:
            The current thickness unit.

        Args:
            unit (blueye.protocol.ThicknessUnit): The thickness unit to set.

        Warns:
            RuntimeWarning: If the unit is not an instance of blueye.protocol.ThicknessUnit.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.thickness_unit

    @thickness_unit.setter
    def thickness_unit(self, unit: blueye.protocol.ThicknessUnit):
        if not isinstance(unit, blueye.protocol.ThicknessUnit):
            warnings.warn("Invalid thickness unit, ignoring", RuntimeWarning)
        else:
            if self._overlay_parametres is None:
                self._update_overlay_parameters()
            self._overlay_parametres.thickness_unit = unit
            self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    @property
    def drone_location_enabled(self) -> bool:
        """Get or set the state of the drone location overlay.

        Returns:
            The current state of the drone location overlay.

        Args:
            enable_drone_location (bool): True to enable the drone location overlay,
                                          False to disable it.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.drone_location_enabled

    @drone_location_enabled.setter
    def drone_location_enabled(self, enable_drone_location: bool):
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.drone_location_enabled = enable_drone_location
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    @property
    def shading(self) -> float:
        """Get or set the pixel intensity to subtract from text background.

        Returns:
            The current shading intensity.

        Args:
            intensity (float): The shading intensity to set. Valid range is 0.0 to 1.0.
                               0 is transparent, 1 is black.

        Warns:
            RuntimeWarning: If the shading intensity is not a float between 0.0 and 1.0.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.shading

    @shading.setter
    def shading(self, intensity: float):
        if intensity < 0.0 or intensity > 1.0:
            warnings.warn("Invalid shading intensity, ignoring", RuntimeWarning)
        else:
            if self._overlay_parametres is None:
                self._update_overlay_parameters()
            self._overlay_parametres.shading = intensity
            self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    @property
    def gamma_ray_measurement_enabled(self) -> bool:
        """Get or set the state of the gamma-ray measurement overlay.

        Returns:
            The current state of the gamma-ray measurement overlay.

        Args:
            enable_gamma_ray_measurement (bool): True to enable the gamma-ray measurement overlay,
                                                 False to disable it.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.medusa_enabled

    @gamma_ray_measurement_enabled.setter
    def gamma_ray_measurement_enabled(self, enable_gamma_ray_measurement: bool):
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.medusa_enabled = enable_gamma_ray_measurement
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    @property
    def timezone_offset(self) -> int:
        """Get or set the timezone offset for the overlay.

        Set to the number of minutes (either positive or negative) the timestamp should be offset.

        Returns:
            The current timezone offset.

        Args:
            offset (int): The timezone offset to set.
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
        """Get or set the margin width for the overlay.

        The amount of pixels to use as margin on the right and left side of the overlay.

        Returns:
            The current margin width.

        Args:
            width (int): The margin width to set. Needs to be a positive integer.

        Warns:
            RuntimeWarning: If the margin width is not a positive integer.
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
        """Get or set the margin height for the overlay.

        The amount of pixels to use as margin on the top and bottom side of the overlay.

        Returns:
            The current margin height.

        Args:
            height (int): The margin height to set. Needs to be a positive integer.
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
        """Get or set the font size for the overlay.

        Needs to be an instance of the `blueye.protocol.FontSize` enum.

        Returns:
            The current font size.

        Args:
            size (blueye.protocol.FontSize): The font size to set.

        Warns:
            RuntimeWarning: If the font size is not an instance of blueye.protocol.FontSize.
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
        """Get or set the title for the overlay.

        The title needs to be a string of only ASCII characters with a maximum length of 63
        characters.

        Set to an empty string to disable title.

        Returns:
            The current title.

        Args:
            input_title (str): The title to set. Truncated to 63 characters if longer.

        Warns:
            RuntimeWarning: If the title is too long or contains non-ASCII characters.
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
        """Get or set the subtitle for the overlay.

        The subtitle needs to be a string of only ASCII characters with a maximum length of 63
        characters.

        Set to an empty string to disable the subtitle.

        Returns:
            The current subtitle.

        Args:
            input_subtitle (str): The subtitle to set. Set to an empty string to disable.
                                  Truncated to 63 characters if longer.

        Warns:
            RuntimeWarning: If the subtitle is too long or contains non-ASCII characters.
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
        """Get or set the format string for the time displayed in the overlay.

        Must be a string containing only ASCII characters, with a max length of 63 characters.

        The format codes are defined by the C89 standard, see
        https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes for an
        overview of the available codes.

        Returns:
            The current date format.

        Args:
            input_format_str (str): The date format string to set.

        Warns:
            RuntimeWarning: If the date format is too long or contains non-ASCII characters.
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
        """Upload user selectable logo for watermarking videos and pictures.

        Set the logo-property to `blueye.protocol.LogoType.LOG_TYPE_CUSTOM` to enable this logo.

        Allowed filetype: JPG or PNG.
        Max resolution: 2000 px.
        Max file size: 5 MB.

        Args:
            path_to_logo (str): The path to the logo file.
            timeout (float, optional): The timeout for the upload request.

        Raises:
            requests.exceptions.HTTPError: If the file is invalid (status code 400).
            requests.exceptions.ConnectTimeout: If unable to create a connection within the
                                                specified timeout.
        """
        with open(path_to_logo, "rb") as f:
            url = f"http://{self._parent_drone._ip}/asset/logo"
            files = {"image": f}
            response = requests.post(url, files=files, timeout=timeout)
        response.raise_for_status()

    def download_logo(self, output_directory=".", timeout: float = 1.0):
        """Download the original user uploaded logo (PNG or JPG).

        Select the download directory with the output_directory parameter.

        Args:
            output_directory (str): The directory to save the downloaded logo.
            timeout (float): The timeout for the download request.

        Raises:
            requests.exceptions.HTTPError: If no custom logo is uploaded.
            requests.exceptions.ConnectTimeout: If unable to create a connection within the
                                                specified timeout.
        """
        response = requests.get(f"http://{self._parent_drone._ip}/asset/logo", timeout=timeout)
        response.raise_for_status()
        filename = re.findall('filename="(.+)"', response.headers["Content-Disposition"])[0]
        with open(f"{output_directory}/{filename}", "wb") as f:
            f.write(response.content)

    def delete_logo(self, timeout: float = 1.0):
        """Delete the user uploaded logo from the drone.

        Args:
            timeout (float): The timeout for the delete request.

        Raises:
            requests.exceptions.HTTPError: If an error occurs during deletion.
            requests.exceptions.ConnectTimeout: If unable to create a connection within the
                                                specified timeout.
        """
        response = requests.delete(f"http://{self._parent_drone._ip}/asset/logo", timeout=timeout)
        response.raise_for_status()


class Camera:
    """Handles the camera functionality for the Blueye drone."""

    def __init__(self, parent_drone: Drone, is_guestport_camera: bool = False):
        """Initialize the Camera class.

        Args:
            parent_drone (Drone): The parent drone instance.
            is_guestport_camera (bool, optional): Whether this is a guestport camera.
        """
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

    def _get_record_state(self) -> Optional[blueye.protocol.RecordState]:
        record_state_tel = self._parent_drone.telemetry.get(blueye.protocol.RecordStateTel)
        if record_state_tel is not None:
            return record_state_tel.record_state
        else:
            return None

    def _update_camera_parameters(self):
        self._camera_parameters = self._parent_drone._req_rep_client.get_camera_parameters(
            camera=self._camera_type
        )

    @property
    def is_recording(self) -> Optional[bool]:
        """Get or set the camera recording state.

        Args:
            start_recording (bool): Set to True to start a recording, set to False to stop the
                                    current recording.

        Returns:
            True if the camera is currently recording, False if not. Returns None if the SDK
            hasn't received a RecordState telemetry message.

        Warns:
            RuntimeWarning: If no recording state telemetry data is received.
        """
        record_state = self._get_record_state()
        if record_state is None:
            return None
        if self._is_guestport_camera:
            return record_state.guestport_is_recording
        else:
            return record_state.main_is_recording

    @is_recording.setter
    def is_recording(self, start_recording: bool):
        record_state = self._get_record_state()
        if record_state is None:
            logger.warning("Unable to set recording state, no record state telemetry received")
            return
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
        """Set or get the video stream bitrate.

        Args:
            bitrate (int): Set the video stream bitrate in bits, valid values are in range
                           (1 000 000 .. 16 000 000).

        Returns:
            The H264 video stream bitrate.
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
        """Set or get the bitrate for the still picture stream.

        Args:
            bitrate (int): Set the still picture stream bitrate in bits, valid values are in range
                           (1 000 000 .. 300 000 000). Default value is 100 000 000.

        Returns:
            The still picture stream bitrate.
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
        """Set or get the camera exposure.

        Args:
            exposure (int): Set the camera exposure time. Unit is thousandths of a second,
                            ie. 5 = 5s/1000. Valid values are in the range (1 .. 5000) or -1
                            for auto exposure.

        Returns:
            The camera exposure.
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
        """Set or get the camera white balance.

        Args:
            white_balance (int): Set the camera white balance. Valid values are in the range
                                 (2800..9300) or -1 for auto white balance.

        Returns:
            The camera white balance.
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
        """Set or get the camera hue.

        Args:
            hue (int): Set the camera hue. Valid values are in the range (-40..40).

        Returns:
            The camera hue.
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
        """Set or get the camera resolution.

        Args:
            resolution (int): Set the camera in vertical pixels. Valid values are 720 or 1080.

        Returns:
            The camera resolution.
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
    def stream_resolution(self) -> blueye.protocol.Resolution:
        """Set or get the camera stream resolution.

        Requires Blunux version >= 4.4. For older versions use the
        [`resolution`][blueye.sdk.camera.Camera.resolution] property.

        Args:
            resolution (blueye.protocol.Resolution): Set the camera stream resolution.

        Raises:
            ValueError: If the resolution is not a valid `blueye.protocol.Resolution` type

        Returns:
            The camera stream resolution
        """
        self._update_camera_parameters()
        return self._camera_parameters.stream_resolution

    @stream_resolution.setter
    def stream_resolution(self, resolution: blueye.protocol.Resolution):
        if not isinstance(resolution, blueye.protocol.Resolution):
            raise ValueError(f"{resolution} is not a valid resolution type")
        if self._camera_parameters is None:
            self._update_camera_parameters()
        self._camera_parameters.stream_resolution = resolution
        self._parent_drone._req_rep_client.set_camera_parameters(self._camera_parameters)

    @property
    def recording_resolution(self) -> blueye.protocol.Resolution:
        """Set or get the camera recording resolution.

        Requires Blunux version >= 4.4. For older versions use the
        [`resolution`][blueye.sdk.camera.Camera.resolution] property.

        Returns:
            The camera recording resolution.
        """
        self._update_camera_parameters()
        return self._camera_parameters.recording_resolution

    @recording_resolution.setter
    def recording_resolution(self, resolution: blueye.protocol.Resolution):
        if not isinstance(resolution, blueye.protocol.Resolution):
            raise ValueError(f"{resolution} is not a valid resolution type")
        if self._camera_parameters is None:
            self._update_camera_parameters()
        self._camera_parameters.recording_resolution = resolution
        self._parent_drone._req_rep_client.set_camera_parameters(self._camera_parameters)

    @property
    def framerate(self) -> int:
        """Set or get the camera frame rate.

        Args:
            framerate (int): Set the camera frame rate in frames per second.
                             Valid values are 25 or 30.

        Returns:
            The camera frame rate.
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
    def record_time(self) -> Optional[int]:
        """Get the duration of the current camera recording.

        Returns:
            The length in seconds of the current recording, -1 if the camera is not currently
            recording. Returns None if the SDK hasn't received a RecordState telemetry message.
        """
        record_state = self._get_record_state()
        if record_state is None:
            return None
        if self._is_guestport_camera:
            return record_state.guestport_seconds
        else:
            return record_state.main_seconds

    def take_picture(self):
        """Take a still picture and store it locally on the drone.

        These pictures can be downloaded with the Blueye App, or by any WebDAV compatible client.
        """
        self._parent_drone._ctrl_client.take_still_picture()
