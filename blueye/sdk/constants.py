"""
This file contains constants used by the SDK.
"""

import blueye.protocol as bp

JETSON_MODELS = frozenset({bp.Model.MODEL_X3_ULTRA, bp.Model.MODEL_X7})
"""Drone models built on the NVIDIA Jetson platform.

These models share the same camera pipeline, which differs from the older models in the camera
controls it offers (no hue control, 60 fps support, main camera calibration published in
`DroneInfoTel`). `MODEL_NEXT` was a retired prototype and is deliberately not included.
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
