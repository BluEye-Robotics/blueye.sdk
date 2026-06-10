"""Tests for the deprecated property shims.

Every property that used to expose drone state/control has been replaced by an explicit
getter/setter method. The old property names are kept as thin shims that emit a
``DeprecationWarning`` and delegate to the new method. This module verifies, for every shim, that:

* reading it warns and delegates to the new getter,
* writing it (when writable) warns and delegates to the new setter,
* writing a read-only shim raises ``AttributeError`` (the original footgun this migration fixes).
"""

import blueye.protocol as bp
import pytest

from blueye.sdk.guestport import Gripper


def _make_gripper(drone):
    return Gripper(
        drone,
        bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_1,
        bp.GuestPortDevice(),
    )


# Each entry: (accessor, property_name, getter_method, setter_method_or_None)
# `accessor` takes the mocked drone and returns the object that owns the deprecated property.
DEPRECATED_PROPERTIES = [
    # Drone
    (lambda d: d, "lights", "get_lights", "set_lights"),
    (lambda d: d, "connected_clients", "get_connected_clients", None),
    (lambda d: d, "client_in_control", "get_client_in_control", None),
    (lambda d: d, "depth", "get_depth", None),
    (lambda d: d, "pose", "get_pose", None),
    (lambda d: d, "altitude", "get_altitude", None),
    (lambda d: d, "error_flags", "get_error_flags", None),
    (lambda d: d, "active_video_streams", "get_active_video_streams", None),
    (lambda d: d, "water_temperature", "get_water_temperature", None),
    (lambda d: d, "dive_time", "get_dive_time", None),
    # Config
    (lambda d: d.config, "water_density", "get_water_density", "set_water_density"),
    # Battery
    (lambda d: d.battery, "state_of_charge", "get_state_of_charge", None),
    # Motion
    (lambda d: d.motion, "surge", "get_surge", "set_surge"),
    (lambda d: d.motion, "sway", "get_sway", "set_sway"),
    (lambda d: d.motion, "heave", "get_heave", "set_heave"),
    (lambda d: d.motion, "yaw", "get_yaw", "set_yaw"),
    (lambda d: d.motion, "boost", "get_boost", "set_boost"),
    (lambda d: d.motion, "slow", "get_slow", "set_slow"),
    (
        lambda d: d.motion,
        "current_thruster_setpoints",
        "get_current_thruster_setpoints",
        None,
    ),
    (lambda d: d.motion, "auto_depth_active", "is_auto_depth_active", "enable_auto_depth"),
    (lambda d: d.motion, "auto_heading_active", "is_auto_heading_active", "enable_auto_heading"),
    (lambda d: d.motion, "auto_altitude_active", "is_auto_altitude_active", "enable_auto_altitude"),
    (
        lambda d: d.motion,
        "station_keeping_active",
        "is_station_keeping_active",
        "enable_station_keeping",
    ),
    (
        lambda d: d.motion,
        "weather_vaning_active",
        "is_weather_vaning_active",
        "enable_weather_vaning",
    ),
    # Gripper
    (_make_gripper, "grip_velocity", "get_grip_velocity", "set_grip_velocity"),
    (_make_gripper, "rotation_velocity", "get_rotation_velocity", "set_rotation_velocity"),
    # Tilt
    (lambda d: d.camera.tilt, "angle", "get_angle", None),
    (
        lambda d: d.camera.tilt,
        "stabilization_enabled",
        "is_stabilization_enabled",
        "enable_stabilization",
    ),
    # Overlay
    (
        lambda d: d.camera.overlay,
        "temperature_enabled",
        "is_temperature_enabled",
        "enable_temperature",
    ),
    (lambda d: d.camera.overlay, "depth_enabled", "is_depth_enabled", "enable_depth"),
    (lambda d: d.camera.overlay, "heading_enabled", "is_heading_enabled", "enable_heading"),
    (lambda d: d.camera.overlay, "tilt_enabled", "is_tilt_enabled", "enable_tilt"),
    (lambda d: d.camera.overlay, "date_enabled", "is_date_enabled", "enable_date"),
    (lambda d: d.camera.overlay, "logo", "get_logo", "set_logo"),
    (lambda d: d.camera.overlay, "depth_unit", "get_depth_unit", "set_depth_unit"),
    (
        lambda d: d.camera.overlay,
        "temperature_unit",
        "get_temperature_unit",
        "set_temperature_unit",
    ),
    (lambda d: d.camera.overlay, "cp_probe_enabled", "is_cp_probe_enabled", "enable_cp_probe"),
    (lambda d: d.camera.overlay, "distance_enabled", "is_distance_enabled", "enable_distance"),
    (lambda d: d.camera.overlay, "altitude_enabled", "is_altitude_enabled", "enable_altitude"),
    (lambda d: d.camera.overlay, "thickness_enabled", "is_thickness_enabled", "enable_thickness"),
    (lambda d: d.camera.overlay, "thickness_unit", "get_thickness_unit", "set_thickness_unit"),
    (
        lambda d: d.camera.overlay,
        "drone_location_enabled",
        "is_drone_location_enabled",
        "enable_drone_location",
    ),
    (lambda d: d.camera.overlay, "shading", "get_shading", "set_shading"),
    (
        lambda d: d.camera.overlay,
        "gamma_ray_measurement_enabled",
        "is_gamma_ray_measurement_enabled",
        "enable_gamma_ray_measurement",
    ),
    (lambda d: d.camera.overlay, "timezone_offset", "get_timezone_offset", "set_timezone_offset"),
    (lambda d: d.camera.overlay, "margin_width", "get_margin_width", "set_margin_width"),
    (lambda d: d.camera.overlay, "margin_height", "get_margin_height", "set_margin_height"),
    (lambda d: d.camera.overlay, "font_size", "get_font_size", "set_font_size"),
    (lambda d: d.camera.overlay, "title", "get_title", "set_title"),
    (lambda d: d.camera.overlay, "subtitle", "get_subtitle", "set_subtitle"),
    (lambda d: d.camera.overlay, "date_format", "get_date_format", "set_date_format"),
    # Camera
    (lambda d: d.camera, "is_recording", "is_recording_active", "set_recording"),
    (lambda d: d.camera, "record_time", "get_record_time", None),
    (lambda d: d.camera, "bitrate", "get_bitrate", "set_bitrate"),
    (
        lambda d: d.camera,
        "bitrate_still_picture",
        "get_bitrate_still_picture",
        "set_bitrate_still_picture",
    ),
    (lambda d: d.camera, "exposure", "get_exposure", "set_exposure"),
    (lambda d: d.camera, "whitebalance", "get_whitebalance", "set_whitebalance"),
    (lambda d: d.camera, "hue", "get_hue", "set_hue"),
    (lambda d: d.camera, "resolution", "get_resolution", "set_resolution"),
    (lambda d: d.camera, "stream_resolution", "get_stream_resolution", "set_stream_resolution"),
    (
        lambda d: d.camera,
        "recording_resolution",
        "get_recording_resolution",
        "set_recording_resolution",
    ),
    (lambda d: d.camera, "framerate", "get_framerate", "set_framerate"),
    (lambda d: d.camera, "recording_codec", "get_recording_codec", "set_recording_codec"),
    (lambda d: d.camera, "recording_bitrate", "get_recording_bitrate", "set_recording_bitrate"),
    (lambda d: d.camera, "streaming_protocol", "get_streaming_protocol", "set_streaming_protocol"),
]

_WRITABLE = [p for p in DEPRECATED_PROPERTIES if p[3] is not None]
_READ_ONLY = [p for p in DEPRECATED_PROPERTIES if p[3] is None]


@pytest.mark.parametrize(
    "accessor,prop,getter,setter", DEPRECATED_PROPERTIES, ids=[p[1] for p in DEPRECATED_PROPERTIES]
)
def test_getter_warns_and_delegates(mocked_drone, mocker, accessor, prop, getter, setter):
    obj = accessor(mocked_drone)
    mock = mocker.patch.object(obj, getter, return_value=mocker.sentinel.value)
    with pytest.warns(DeprecationWarning, match=getter):
        result = getattr(obj, prop)
    assert result is mocker.sentinel.value
    mock.assert_called_once_with()


@pytest.mark.parametrize("accessor,prop,getter,setter", _WRITABLE, ids=[p[1] for p in _WRITABLE])
def test_setter_warns_and_delegates(mocked_drone, mocker, accessor, prop, getter, setter):
    obj = accessor(mocked_drone)
    mock = mocker.patch.object(obj, setter)
    with pytest.warns(DeprecationWarning, match=setter):
        setattr(obj, prop, True)
    mock.assert_called_once_with(True)


@pytest.mark.parametrize("accessor,prop,getter,setter", _READ_ONLY, ids=[p[1] for p in _READ_ONLY])
def test_readonly_assignment_raises(mocked_drone, accessor, prop, getter, setter):
    obj = accessor(mocked_drone)
    with pytest.raises(AttributeError):
        setattr(obj, prop, True)


def test_setpoints_setter_keeps_helpful_error_message(mocked_drone):
    """The current_thruster_setpoints shim keeps its dedicated, helpful error message."""
    with pytest.raises(AttributeError, match="Do not set the setpoints directly"):
        mocked_drone.motion.current_thruster_setpoints = {}
