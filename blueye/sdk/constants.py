"""
This file contains constants used by the SDK.
"""

import blueye.protocol as bp

JETSON_MODELS = frozenset({bp.Model.MODEL_X3_ULTRA, bp.Model.MODEL_X7})
"""Drone models built on the NVIDIA Jetson platform.

These models have the 4K camera, which differs from the camera in the older models in the
controls it offers (no hue control, 60 fps support, main camera calibration published in
`DroneInfoTel`). `MODEL_NEXT` was a retired prototype and is not included.
"""

EVENT_DRIVEN_TELEMETRY = frozenset(
    {
        bp.AquaTrollProbeMetadataTel,
        bp.AquaTrollSensorMetadataTel,
        bp.AquaTrollSensorParametersTel,
        bp.CameraPanTiltZoomTel,
        bp.ColorCorrectionTel,
        bp.GnssStatusTel,
        bp.LaserTel,
        bp.LogEntryTel,
        bp.MultibeamConfigTel,
        bp.MultibeamPingTel,
        bp.ObjectDetectionsTel,
        bp.RemovableStorageTel,
        bp.SotStateTel,
        bp.TurbidityFilterTel,
    }
)
"""Telemetry messages the drone publishes when their data arrives rather than on a timer.

A new sonar ping, a detection, a changed camera filter or a plugged-in storage device is
published as it happens, so these messages have no publish frequency and
[`set_msg_publish_frequency`][blueye.sdk.drone.Telemetry.set_msg_publish_frequency] raises for
them. Messages from peripherals are also only published while the peripheral is connected.
"""


class WaterDensities:
    """
    Various typical densities for water (in grams/liter).

    Attributes:
        fresh (float): Density of fresh water.
        brackish (float): Density of brackish water.
        salty (float): Density of salty water.
    """

    fresh = 997.0
    brackish = 1011.0
    salty = 1025.0
