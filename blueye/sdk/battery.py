from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import blueye.protocol

# Necessary to avoid cyclic imports
if TYPE_CHECKING:
    from .drone import Drone


class Battery:
    def __init__(self, parent_drone: Drone):
        self._parent_drone = parent_drone

    @property
    def state_of_charge(self) -> Optional[float]:
        """Get the battery state of charge

        *Returns*:

        * Current state of charge of the drone battery (0..1)
        """
        battery_tel = self._parent_drone.telemetry.get(blueye.protocol.BatteryTel)
        if battery_tel is not None:
            return battery_tel.battery.level
        else:
            return None
