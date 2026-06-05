from __future__ import annotations

import logging
import re
import warnings
from typing import TYPE_CHECKING, Optional

import blueye.protocol
import requests
from packaging import version

from .utils import deprecated_property

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

    def get_angle(self) -> Optional[float]:
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

    angle = deprecated_property("get_angle")

    def is_stabilization_enabled(self) -> Optional[bool]:
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

    def enable_stabilization(self, enabled: bool):
        """Set the state of active camera stabilization.

        Args:
            enabled (bool): True to turn stabilization on, False to turn it off.

        Raises:
            RuntimeError: If the connected drone does not have the tilt option.
        """
        self._verify_tilt_in_features()
        self._parent_drone._ctrl_client.set_tilt_stabilization(enabled)

    stabilization_enabled = deprecated_property("is_stabilization_enabled", "enable_stabilization")


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

    def is_temperature_enabled(self) -> bool:
        """Get the state of the temperature overlay.

        Returns:
            The current state of the temperature overlay.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.temperature_enabled

    def enable_temperature(self, enable_temperature: bool):
        """Set the state of the temperature overlay.

        Args:
            enable_temperature (bool): True to enable the temperature overlay, False to disable it.
        """
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.temperature_enabled = enable_temperature
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    temperature_enabled = deprecated_property("is_temperature_enabled", "enable_temperature")

    def is_depth_enabled(self) -> bool:
        """Get the state of the depth overlay.

        Returns:
            The current state of the depth overlay.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.depth_enabled

    def enable_depth(self, enable_depth: bool):
        """Set the state of the depth overlay.

        Args:
            enable_depth (bool): True to enable the depth overlay, False to disable it.
        """
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.depth_enabled = enable_depth
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    depth_enabled = deprecated_property("is_depth_enabled", "enable_depth")

    def is_heading_enabled(self) -> bool:
        """Get the state of the heading overlay.

        Returns:
            The current state of the heading overlay.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.heading_enabled

    def enable_heading(self, enable_heading: bool):
        """Set the state of the heading overlay.

        Args:
            enable_heading (bool): True to enable the heading overlay, False to disable it.
        """
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.heading_enabled = enable_heading
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    heading_enabled = deprecated_property("is_heading_enabled", "enable_heading")

    def is_tilt_enabled(self) -> bool:
        """Get the state of the tilt overlay.

        Returns:
            The current state of the tilt overlay.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.tilt_enabled

    def enable_tilt(self, enable_tilt: bool):
        """Set the state of the tilt overlay.

        Args:
            enable_tilt (bool): True to enable the tilt overlay, False to disable it.
        """
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.tilt_enabled = enable_tilt
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    tilt_enabled = deprecated_property("is_tilt_enabled", "enable_tilt")

    def is_date_enabled(self) -> bool:
        """Get the state of the date overlay.

        Returns:
            The current state of the date overlay.
        """
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        return self._overlay_parametres.date_enabled

    def enable_date(self, enable_date: bool):
        """Set the state of the date overlay.

        Args:
            enable_date (bool): True to enable the date overlay, False to disable it.
        """
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.date_enabled = enable_date
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    date_enabled = deprecated_property("is_date_enabled", "enable_date")

    def get_logo(self) -> blueye.protocol.LogoType:
        """Get the logo overlay selection.

        Returns:
            The current logo type.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.logo_type

    def set_logo(self, logo_type: blueye.protocol.LogoType):
        """Set the logo overlay selection.

        Args:
            logo_type (blueye.protocol.LogoType): The logo type.

        Warns:
            RuntimeWarning: If the logo type is not an instance of blueye.protocol.LogoType.
        """
        if not isinstance(logo_type, blueye.protocol.LogoType):
            warnings.warn("Invalid logo type, ignoring", RuntimeWarning)
        else:
            if self._overlay_parametres is None:
                self._update_overlay_parameters()
            self._overlay_parametres.logo_type = logo_type
            self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    logo = deprecated_property("get_logo", "set_logo")

    def get_depth_unit(self) -> blueye.protocol.DepthUnit:
        """Get the depth unit for the overlay.

        Returns:
            The current depth unit.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.depth_unit

    def set_depth_unit(self, unit: blueye.protocol.DepthUnit):
        """Set the depth unit for the overlay.

        Args:
            unit (blueye.protocol.DepthUnit): The depth unit to set.

        Warns:
            RuntimeWarning: If the unit is not an instance of blueye.protocol.DepthUnit.
        """
        if not isinstance(unit, blueye.protocol.DepthUnit):
            warnings.warn("Invalid depth unit, ignoring", RuntimeWarning)
        else:
            if self._overlay_parametres is None:
                self._update_overlay_parameters()
            self._overlay_parametres.depth_unit = unit
            self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    depth_unit = deprecated_property("get_depth_unit", "set_depth_unit")

    def get_temperature_unit(self) -> blueye.protocol.TemperatureUnit:
        """Get the temperature unit for the overlay.

        Returns:
            The current temperature unit.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.temperature_unit

    def set_temperature_unit(self, unit: blueye.protocol.TemperatureUnit):
        """Set the temperature unit for the overlay.

        Args:
            unit (blueye.protocol.TemperatureUnit): The temperature unit to set.

        Warns:
            RuntimeWarning: If the unit is not an instance of blueye.protocol.TemperatureUnit.
        """
        if not isinstance(unit, blueye.protocol.TemperatureUnit):
            warnings.warn("Invalid temperature unit, ignoring", RuntimeWarning)
        else:
            if self._overlay_parametres is None:
                self._update_overlay_parameters()
            self._overlay_parametres.temperature_unit = unit
            self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    temperature_unit = deprecated_property("get_temperature_unit", "set_temperature_unit")

    def is_cp_probe_enabled(self) -> bool:
        """Get the state of the CP probe overlay.

        Returns:
            The current state of the CP probe overlay.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.cp_probe_enabled

    def enable_cp_probe(self, enable_cp_probe: bool):
        """Set the state of the CP probe overlay.

        Args:
            enable_cp_probe (bool): True to enable the CP probe overlay, False to disable it.
        """
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.cp_probe_enabled = enable_cp_probe
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    cp_probe_enabled = deprecated_property("is_cp_probe_enabled", "enable_cp_probe")

    def is_distance_enabled(self) -> bool:
        """Get the state of the distance overlay.

        Returns:
            The current state of the distance overlay.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.distance_enabled

    def enable_distance(self, enable_distance: bool):
        """Set the state of the distance overlay.

        Args:
            enable_distance (bool): True to enable the distance overlay, False to disable it.
        """
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.distance_enabled = enable_distance
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    distance_enabled = deprecated_property("is_distance_enabled", "enable_distance")

    def is_altitude_enabled(self) -> bool:
        """Get the state of the altitude overlay.

        Returns:
            The current state of the altitude overlay.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.altitude_enabled

    def enable_altitude(self, enable_altitude: bool):
        """Set the state of the altitude overlay.

        Args:
            enable_altitude (bool): True to enable the altitude overlay, False to disable it.
        """
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.altitude_enabled = enable_altitude
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    altitude_enabled = deprecated_property("is_altitude_enabled", "enable_altitude")

    def is_thickness_enabled(self) -> bool:
        """Get the state of the thickness overlay.

        Returns:
            The current state of the thickness overlay.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.thickness_enabled

    def enable_thickness(self, enable_thickness: bool):
        """Set the state of the thickness overlay.

        Args:
            enable_thickness (bool): True to enable the thickness overlay, False to disable it.
        """
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.thickness_enabled = enable_thickness
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    thickness_enabled = deprecated_property("is_thickness_enabled", "enable_thickness")

    def get_thickness_unit(self) -> blueye.protocol.ThicknessUnit:
        """Get the thickness unit for the overlay.

        Returns:
            The current thickness unit.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.thickness_unit

    def set_thickness_unit(self, unit: blueye.protocol.ThicknessUnit):
        """Set the thickness unit for the overlay.

        Args:
            unit (blueye.protocol.ThicknessUnit): The thickness unit to set.

        Warns:
            RuntimeWarning: If the unit is not an instance of blueye.protocol.ThicknessUnit.
        """
        if not isinstance(unit, blueye.protocol.ThicknessUnit):
            warnings.warn("Invalid thickness unit, ignoring", RuntimeWarning)
        else:
            if self._overlay_parametres is None:
                self._update_overlay_parameters()
            self._overlay_parametres.thickness_unit = unit
            self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    thickness_unit = deprecated_property("get_thickness_unit", "set_thickness_unit")

    def is_drone_location_enabled(self) -> bool:
        """Get the state of the drone location overlay.

        Returns:
            The current state of the drone location overlay.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.drone_location_enabled

    def enable_drone_location(self, enable_drone_location: bool):
        """Set the state of the drone location overlay.

        Args:
            enable_drone_location (bool): True to enable the drone location overlay,
                                          False to disable it.
        """
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.drone_location_enabled = enable_drone_location
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    drone_location_enabled = deprecated_property(
        "is_drone_location_enabled", "enable_drone_location"
    )

    def get_shading(self) -> float:
        """Get the pixel intensity to subtract from text background.

        Returns:
            The current shading intensity.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.shading

    def set_shading(self, intensity: float):
        """Set the pixel intensity to subtract from text background.

        Args:
            intensity (float): The shading intensity to set. Valid range is 0.0 to 1.0.
                               0 is transparent, 1 is black.

        Warns:
            RuntimeWarning: If the shading intensity is not a float between 0.0 and 1.0.
        """
        if intensity < 0.0 or intensity > 1.0:
            warnings.warn("Invalid shading intensity, ignoring", RuntimeWarning)
        else:
            if self._overlay_parametres is None:
                self._update_overlay_parameters()
            self._overlay_parametres.shading = intensity
            self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    shading = deprecated_property("get_shading", "set_shading")

    def is_gamma_ray_measurement_enabled(self) -> bool:
        """Get the state of the gamma-ray measurement overlay.

        Returns:
            The current state of the gamma-ray measurement overlay.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.medusa_enabled

    def enable_gamma_ray_measurement(self, enable_gamma_ray_measurement: bool):
        """Set the state of the gamma-ray measurement overlay.

        Args:
            enable_gamma_ray_measurement (bool): True to enable the gamma-ray measurement overlay,
                                                 False to disable it.
        """
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.medusa_enabled = enable_gamma_ray_measurement
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    gamma_ray_measurement_enabled = deprecated_property(
        "is_gamma_ray_measurement_enabled", "enable_gamma_ray_measurement"
    )

    def get_timezone_offset(self) -> int:
        """Get the timezone offset for the overlay.

        Returns:
            The current timezone offset.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.timezone_offset

    def set_timezone_offset(self, offset: int):
        """Set the timezone offset for the overlay.

        Set to the number of minutes (either positive or negative) the timestamp should be offset.

        Args:
            offset (int): The timezone offset to set.
        """
        if self._overlay_parametres is None:
            self._update_overlay_parameters()
        self._overlay_parametres.timezone_offset = offset
        self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    timezone_offset = deprecated_property("get_timezone_offset", "set_timezone_offset")

    def get_margin_width(self) -> int:
        """Get the margin width for the overlay.

        Returns:
            The current margin width.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.margin_width

    def set_margin_width(self, width: int):
        """Set the margin width for the overlay.

        The amount of pixels to use as margin on the right and left side of the overlay.

        Args:
            width (int): The margin width to set. Needs to be a positive integer.

        Warns:
            RuntimeWarning: If the margin width is not a positive integer.
        """
        if width < 0:
            warnings.warn("Invalid margin width, ignoring", RuntimeWarning)
        else:
            if self._overlay_parametres is None:
                self._update_overlay_parameters()
            self._overlay_parametres.margin_width = width
            self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    margin_width = deprecated_property("get_margin_width", "set_margin_width")

    def get_margin_height(self) -> int:
        """Get the margin height for the overlay.

        Returns:
            The current margin height.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.margin_height

    def set_margin_height(self, height: int):
        """Set the margin height for the overlay.

        The amount of pixels to use as margin on the top and bottom side of the overlay.

        Args:
            height (int): The margin height to set. Needs to be a positive integer.

        Warns:
            RuntimeWarning: If the margin height is not a positive integer.
        """
        if height < 0:
            warnings.warn("Invalid margin height, ignoring", RuntimeWarning)
        else:
            if self._overlay_parametres is None:
                self._update_overlay_parameters()
            self._overlay_parametres.margin_height = height
            self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    margin_height = deprecated_property("get_margin_height", "set_margin_height")

    def get_font_size(self) -> blueye.protocol.FontSize:
        """Get the font size for the overlay.

        Returns:
            The current font size.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.font_size

    def set_font_size(self, size: blueye.protocol.FontSize):
        """Set the font size for the overlay.

        Needs to be an instance of the `blueye.protocol.FontSize` enum.

        Args:
            size (blueye.protocol.FontSize): The font size to set.

        Warns:
            RuntimeWarning: If the font size is not an instance of blueye.protocol.FontSize.
        """
        if not isinstance(size, blueye.protocol.FontSize):
            warnings.warn("Invalid font size, ignoring", RuntimeWarning)
        else:
            if self._overlay_parametres is None:
                self._update_overlay_parameters()
            self._overlay_parametres.font_size = size
            self._parent_drone._req_rep_client.set_overlay_parameters(self._overlay_parametres)

    font_size = deprecated_property("get_font_size", "set_font_size")

    def get_title(self) -> str:
        """Get the title for the overlay.

        Returns:
            The current title.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.title

    def set_title(self, input_title: str):
        """Set the title for the overlay.

        The title needs to be a string of only ASCII characters with a maximum length of 63
        characters.

        Set to an empty string to disable title.

        Args:
            input_title (str): The title to set. Truncated to 63 characters if longer.

        Warns:
            RuntimeWarning: If the title is too long or contains non-ASCII characters.
        """
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

    title = deprecated_property("get_title", "set_title")

    def get_subtitle(self) -> str:
        """Get the subtitle for the overlay.

        Returns:
            The current subtitle.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.subtitle

    def set_subtitle(self, input_subtitle: str):
        """Set the subtitle for the overlay.

        The subtitle needs to be a string of only ASCII characters with a maximum length of 63
        characters.

        Set to an empty string to disable the subtitle.

        Args:
            input_subtitle (str): The subtitle to set. Set to an empty string to disable.
                                  Truncated to 63 characters if longer.

        Warns:
            RuntimeWarning: If the subtitle is too long or contains non-ASCII characters.
        """
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

    subtitle = deprecated_property("get_subtitle", "set_subtitle")

    def get_date_format(self) -> str:
        """Get the format string for the time displayed in the overlay.

        Returns:
            The current date format.
        """
        self._update_overlay_parameters()
        return self._overlay_parametres.date_format

    def set_date_format(self, input_format_str: str):
        """Set the format string for the time displayed in the overlay.

        Must be a string containing only ASCII characters, with a max length of 63 characters.

        The format codes are defined by the C89 standard, see
        https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes for an
        overview of the available codes.

        Args:
            input_format_str (str): The date format string to set.

        Warns:
            RuntimeWarning: If the date format is too long or contains non-ASCII characters.
        """
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

    date_format = deprecated_property("get_date_format", "set_date_format")

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

    class _ParamsBatch:
        """Context manager for batching camera parameter changes.

        Changes are accumulated and sent as a single request on scope exit.

        Usage::

            with drone.camera.configure() as params:
                params.recording_codec = bp.RecordingCodec.RECORDING_CODEC_H265
                params.recording_bitrate = 20_000_000
                params.framerate = bp.Framerate.FRAMERATE_FPS_30
            # All three fields are sent in one set_camera_parameters call here.
        """

        def __init__(self, camera: Camera, timeout: float = 0.5):
            self._camera = camera
            self._timeout = timeout
            self._camera._update_camera_parameters(timeout=timeout)
            self._params = camera._camera_parameters

        def __getattr__(self, name):
            return getattr(self._params, name)

        _VERSION_GATED_PARAMS = {
            "recording_bitrate": "5.0.0",
            "recording_codec": "5.0.0",
        }

        def __setattr__(self, name, value):
            if name.startswith("_"):
                super().__setattr__(name, value)
            else:
                if name in self._VERSION_GATED_PARAMS:
                    self._camera._parent_drone._verify_required_blunux_version(
                        self._VERSION_GATED_PARAMS[name]
                    )
                setattr(self._params, name, value)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is None:
                self._camera._parent_drone._req_rep_client.set_camera_parameters(
                    self._params, timeout=self._timeout
                )
            return False

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

    def _update_camera_parameters(self, timeout: float = 0.5):
        self._camera_parameters = self._parent_drone._req_rep_client.get_camera_parameters(
            camera=self._camera_type, timeout=timeout
        )

    def configure(self, timeout: float = 0.5) -> _ParamsBatch:
        """Return a context manager for batching camera parameter changes.

        All attribute assignments on the returned object are accumulated and sent as a single
        ``set_camera_parameters`` request when the ``with`` block exits.  If an exception is
        raised inside the block the changes are discarded.

        Args:
            timeout (float, optional): Timeout in seconds for the request. Increase when changing
                parameters that trigger pipeline restarts (e.g. codec, resolution).

        Usage::

            with drone.camera.configure() as params:
                params.recording_codec = bp.RecordingCodec.RECORDING_CODEC_H265
                params.recording_bitrate = 20_000_000
            # sent here
        """
        return self._ParamsBatch(self, timeout=timeout)

    def is_recording_active(self) -> Optional[bool]:
        """Get the camera recording state.

        Returns:
            True if the camera is currently recording, False if not. Returns None if the SDK
            hasn't received a RecordState telemetry message.
        """
        record_state = self._get_record_state()
        if record_state is None:
            return None
        if self._is_guestport_camera:
            return record_state.guestport_is_recording
        else:
            return record_state.main_is_recording

    def set_recording(self, start_recording: bool):
        """Set the camera recording state.

        Args:
            start_recording (bool): Set to True to start a recording, set to False to stop the
                                    current recording.

        Warns:
            RuntimeWarning: If no recording state telemetry data is received.
        """
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

    is_recording = deprecated_property("is_recording_active", "set_recording")

    def get_bitrate(self) -> int:
        """Get the video stream bitrate.

        Returns:
            The H264 video stream bitrate.
        """
        self._update_camera_parameters()
        return self._camera_parameters.h264_bitrate

    def set_bitrate(self, bitrate: int):
        """Set the video stream bitrate.

        Args:
            bitrate (int): Set the video stream bitrate in bits, valid values are in range
                           (1 000 000 .. 16 000 000).
        """
        if self._camera_parameters is None:
            self._update_camera_parameters()
        self._camera_parameters.h264_bitrate = bitrate
        self._parent_drone._req_rep_client.set_camera_parameters(self._camera_parameters)

    bitrate = deprecated_property("get_bitrate", "set_bitrate")

    def get_bitrate_still_picture(self) -> int:
        """Get the bitrate for the still picture stream.

        Returns:
            The still picture stream bitrate.
        """
        self._update_camera_parameters()
        return self._camera_parameters.mjpg_bitrate

    def set_bitrate_still_picture(self, bitrate: int):
        """Set the bitrate for the still picture stream.

        Args:
            bitrate (int): Set the still picture stream bitrate in bits, valid values are in range
                           (1 000 000 .. 300 000 000). Default value is 100 000 000.
        """
        if self._camera_parameters is None:
            self._update_camera_parameters()
        self._camera_parameters.mjpg_bitrate = bitrate
        self._parent_drone._req_rep_client.set_camera_parameters(self._camera_parameters)

    bitrate_still_picture = deprecated_property(
        "get_bitrate_still_picture", "set_bitrate_still_picture"
    )

    def get_exposure(self) -> int:
        """Get the camera exposure.

        Returns:
            The camera exposure.
        """
        self._update_camera_parameters()
        return self._camera_parameters.exposure

    def set_exposure(self, exposure: int):
        """Set the camera exposure.

        Args:
            exposure (int): Set the camera exposure time. Unit is thousandths of a second,
                            ie. 5 = 5s/1000. Valid values are in the range (1 .. 5000) or -1
                            for auto exposure.
        """
        if self._camera_parameters is None:
            self._update_camera_parameters()
        self._camera_parameters.exposure = exposure
        self._parent_drone._req_rep_client.set_camera_parameters(self._camera_parameters)

    exposure = deprecated_property("get_exposure", "set_exposure")

    def get_whitebalance(self) -> int:
        """Get the camera white balance.

        Returns:
            The camera white balance.
        """
        self._update_camera_parameters()
        return self._camera_parameters.white_balance

    def set_whitebalance(self, white_balance: int):
        """Set the camera white balance.

        Args:
            white_balance (int): Set the camera white balance. Valid values are in the range
                                 (2800..9300) or -1 for auto white balance.
        """
        if self._camera_parameters is None:
            self._update_camera_parameters()
        self._camera_parameters.white_balance = white_balance
        self._parent_drone._req_rep_client.set_camera_parameters(self._camera_parameters)

    whitebalance = deprecated_property("get_whitebalance", "set_whitebalance")

    def get_hue(self) -> int:
        """Get the camera hue.

        Returns:
            The camera hue.
        """
        self._update_camera_parameters()
        return self._camera_parameters.hue

    def set_hue(self, hue: int):
        """Set the camera hue.

        Args:
            hue (int): Set the camera hue. Valid values are in the range (-40..40).
        """
        if self._camera_parameters is None:
            self._update_camera_parameters()
        self._camera_parameters.hue = hue
        self._parent_drone._req_rep_client.set_camera_parameters(self._camera_parameters)

    hue = deprecated_property("get_hue", "set_hue")

    def get_resolution(self) -> int:
        """Get the camera resolution.

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

    def set_resolution(self, resolution: int):
        """Set the camera resolution.

        Args:
            resolution (int): Set the camera in vertical pixels. Valid values are 720 or 1080.

        Raises:
            ValueError: If the resolution is not 720 or 1080.
        """
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

    resolution = deprecated_property("get_resolution", "set_resolution")

    def get_stream_resolution(self) -> blueye.protocol.Resolution:
        """Get the camera stream resolution.

        For drones running blunux version < 4.4.1 this is the same as the
        [`get_resolution`][blueye.sdk.camera.Camera.get_resolution] method.

        Returns:
            The camera stream resolution
        """
        self._update_camera_parameters()

        # Drones running Blunux < 4.4 do not support stream resolution so we return the old
        # resolution field instead.
        if version.parse(self._parent_drone.software_version_short) < version.parse("4.4"):
            return self._camera_parameters.resolution
        else:
            return self._camera_parameters.stream_resolution

    def set_stream_resolution(self, resolution: blueye.protocol.Resolution):
        """Set the camera stream resolution.

        For drones running blunux version < 4.4.1 this is the same as the
        [`set_resolution`][blueye.sdk.camera.Camera.set_resolution] method.

        Args:
            resolution (blueye.protocol.Resolution): Set the camera stream resolution.

        Raises:
            ValueError: If the resolution is not a valid `blueye.protocol.Resolution` type
        """
        if not isinstance(resolution, blueye.protocol.Resolution):
            raise ValueError(f"{resolution} is not a valid resolution type")
        if self._camera_parameters is None:
            self._update_camera_parameters()
        self._camera_parameters.stream_resolution = resolution
        # If the drone is running Blunux < 4.4 we need to set the resolution field as well.
        self._camera_parameters.resolution = resolution
        self._parent_drone._req_rep_client.set_camera_parameters(self._camera_parameters)

    stream_resolution = deprecated_property("get_stream_resolution", "set_stream_resolution")

    def get_recording_resolution(self) -> blueye.protocol.Resolution:
        """Get the camera recording resolution.

        For drones running Blunux version < 4.4.1 this is the same as the
        [`get_resolution`][blueye.sdk.camera.Camera.get_resolution] method.

        Returns:
            The camera recording resolution.
        """
        self._update_camera_parameters()

        # Drones running Blunux < 4.4 do not support recording resolution so we return the old
        # resolution field instead.
        if version.parse(self._parent_drone.software_version_short) < version.parse("4.4"):
            return self._camera_parameters.resolution
        else:
            return self._camera_parameters.recording_resolution

    def set_recording_resolution(self, resolution: blueye.protocol.Resolution):
        """Set the camera recording resolution.

        For drones running Blunux version < 4.4.1 this is the same as the
        [`set_resolution`][blueye.sdk.camera.Camera.set_resolution] method.

        Args:
            resolution (blueye.protocol.Resolution): Set the camera recording resolution.

        Raises:
            ValueError: If the resolution is not a valid `blueye.protocol.Resolution` type
        """
        if not isinstance(resolution, blueye.protocol.Resolution):
            raise ValueError(f"{resolution} is not a valid resolution type")
        if self._camera_parameters is None:
            self._update_camera_parameters()
        self._camera_parameters.recording_resolution = resolution
        # If the drone is running Blunux < 4.4 we need to set the resolution field as well.
        self._camera_parameters.resolution = resolution
        self._parent_drone._req_rep_client.set_camera_parameters(self._camera_parameters)

    recording_resolution = deprecated_property(
        "get_recording_resolution", "set_recording_resolution"
    )

    def get_framerate(self) -> int:
        """Get the camera frame rate.

        Returns:
            The camera frame rate.
        """
        self._update_camera_parameters()
        if self._camera_parameters.framerate == blueye.protocol.Framerate.FRAMERATE_FPS_25:
            return 25
        elif self._camera_parameters.framerate == blueye.protocol.Framerate.FRAMERATE_FPS_30:
            return 30

    def set_framerate(self, framerate: int):
        """Set the camera frame rate.

        Args:
            framerate (int): Set the camera frame rate in frames per second.
                             Valid values are 25 or 30.

        Raises:
            ValueError: If the framerate is not 25 or 30.
        """
        if framerate not in (25, 30):
            raise ValueError(f"{framerate} is not a valid framerate. Valid values are 25 or 30")
        if self._camera_parameters is None:
            self._update_camera_parameters()
        if framerate == 25:
            self._camera_parameters.framerate = blueye.protocol.Framerate.FRAMERATE_FPS_25
        elif framerate == 30:
            self._camera_parameters.framerate = blueye.protocol.Framerate.FRAMERATE_FPS_30
        self._parent_drone._req_rep_client.set_camera_parameters(self._camera_parameters)

    framerate = deprecated_property("get_framerate", "set_framerate")

    def get_recording_codec(self) -> blueye.protocol.RecordingCodec:
        """Get the recording video codec.

        Returns:
            The current recording codec setting.
        """
        self._update_camera_parameters()
        return self._camera_parameters.recording_codec

    def set_recording_codec(self, codec: blueye.protocol.RecordingCodec):
        """Set the recording video codec.

        Args:
            codec (blueye.protocol.RecordingCodec): Set the recording codec.
                RECORDING_CODEC_UNSPECIFIED uses the platform default (H.264).
                RECORDING_CODEC_H265 is only available on Ultra.

        Raises:
            ValueError: If the codec is not a valid `blueye.protocol.RecordingCodec` type.
            RuntimeError: If the connected drone is running Blunux older than 5.0.0.
        """
        self._parent_drone._verify_required_blunux_version("5.0.0")
        if not isinstance(codec, blueye.protocol.RecordingCodec):
            raise ValueError(f"{codec} is not a valid RecordingCodec type")
        if self._camera_parameters is None:
            self._update_camera_parameters()
        self._camera_parameters.recording_codec = codec
        self._parent_drone._req_rep_client.set_camera_parameters(self._camera_parameters)

    recording_codec = deprecated_property("get_recording_codec", "set_recording_codec")

    def get_recording_bitrate(self) -> int:
        """Get the recording bitrate in bits per second.

        A value of 0 means the drone will auto-compute a default bitrate based on the current
        resolution, framerate, and codec.

        Returns:
            The current recording bitrate in bits per second (0 if automatic).
        """
        self._update_camera_parameters()
        return self._camera_parameters.recording_bitrate

    def set_recording_bitrate(self, bitrate: int):
        """Set the recording bitrate in bits per second.

        A value of 0 means the drone will auto-compute a default bitrate based on the current
        resolution, framerate, and codec.

        Args:
            bitrate (int): Set the recording bitrate in bits per second. Use 0 for automatic.

        Raises:
            RuntimeError: If the connected drone is running Blunux older than 5.0.0.
        """
        self._parent_drone._verify_required_blunux_version("5.0.0")
        if self._camera_parameters is None:
            self._update_camera_parameters()
        self._camera_parameters.recording_bitrate = bitrate
        self._parent_drone._req_rep_client.set_camera_parameters(self._camera_parameters)

    recording_bitrate = deprecated_property("get_recording_bitrate", "set_recording_bitrate")

    def get_streaming_protocol(self) -> blueye.protocol.StreamingProtocol:
        """Get the streaming protocol (codec used for the RTSP stream).

        Returns:
            The current streaming protocol.
        """
        self._update_camera_parameters()
        return self._camera_parameters.streaming_protocol

    def set_streaming_protocol(self, protocol: blueye.protocol.StreamingProtocol):
        """Set the streaming protocol (codec used for the RTSP stream).

        Args:
            protocol (blueye.protocol.StreamingProtocol): Set the streaming protocol.

        Raises:
            ValueError: If the protocol is not a valid `blueye.protocol.StreamingProtocol` type.
        """
        if not isinstance(protocol, blueye.protocol.StreamingProtocol):
            raise ValueError(f"{protocol} is not a valid StreamingProtocol type")
        if self._camera_parameters is None:
            self._update_camera_parameters()
        self._camera_parameters.streaming_protocol = protocol
        self._parent_drone._req_rep_client.set_camera_parameters(self._camera_parameters)

    streaming_protocol = deprecated_property("get_streaming_protocol", "set_streaming_protocol")

    def get_record_time(self) -> Optional[int]:
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

    record_time = deprecated_property("get_record_time")

    def take_picture(self):
        """Take a still picture and store it locally on the drone.

        These pictures can be downloaded with the Blueye App, or by any WebDAV compatible client.
        """
        self._parent_drone._ctrl_client.take_still_picture()
