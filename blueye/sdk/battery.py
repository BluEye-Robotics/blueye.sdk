from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

import blueye.protocol

from .utils import deprecated_property

# Necessary to avoid cyclic imports
if TYPE_CHECKING:
    from .drone import Drone


class Battery:
    """Contains the battery related functions.

    The getters come in two groups:

    * The aggregated getters `get_state_of_charge()`, `get_voltage()` and `get_temperature()`
      return a single value for the drone as a whole, i.e. the value to act on when deciding
      whether to continue or abort a dive. Their meaning does not depend on how many packs the
      drone has or on how the drone combines them.
    * The per-pack getters `get_packs()` and `get_details()` return the data for each physical
      battery pack in slot order, so callers can inspect the packs individually.

    Drones with a single battery (e.g. the X1 and X3) report one pack, and the aggregated getters
    simply return its values. The X7 runs two battery packs in parallel and currently reports each
    pack separately without combining them, so the SDK reduces them the same way the Blueye app
    does: the lowest level, the lowest voltage and the highest temperature across the packs. This
    keeps a weak or depleted pack from being hidden behind a healthy one. If a future drone
    reports a combined value for the parallel packs, the aggregated getters will return that
    value instead, while the per-pack getters keep returning the individual packs.

    Use `has_second_battery()` to check whether a pack is present in the second slot.

    All getters return `None` until the drone has sent the corresponding telemetry message.
    """

    def __init__(self, parent_drone: Drone):
        """Initialize the Battery class.

        Args:
            parent_drone (Drone): The parent drone instance."""
        self._parent_drone = parent_drone

    def _get_battery_tel(self) -> Optional[blueye.protocol.BatteryTel]:
        return self._parent_drone.telemetry.get(blueye.protocol.BatteryTel)

    @staticmethod
    def _packs_from_tel(
        tel: blueye.protocol.BatteryTel | blueye.protocol.BatteryBQ40Z50Tel,
    ) -> List[blueye.protocol.Battery | blueye.protocol.BatteryBQ40Z50]:
        # An unset sub-message reads as a zeroed message, so presence has to be tested explicitly
        # rather than by looking at the field values.
        packs = [tel.battery]
        if "second_battery" in tel:
            packs.append(tel.second_battery)
        return packs

    def has_second_battery(self) -> Optional[bool]:
        """Check if a battery pack is present in the drone's second battery slot.

        Returns:
            True if the drone reports a pack in its second slot (e.g. the X7), False if it reports
            a single pack, or None if no battery telemetry has been received yet.
        """
        battery_tel = self._get_battery_tel()
        if battery_tel is None:
            return None
        return "second_battery" in battery_tel

    def get_packs(self) -> Optional[List[blueye.protocol.Battery]]:
        """Get the essential information for each physical battery pack.

        Returns:
            A list with one `blueye.protocol.Battery` message per pack in slot order, with level
            (0..1), voltage (V) and temperature (°C). Single battery drones return a list with one
            entry, the X7 returns two entries while a pack is present in the second slot. None if
            no battery telemetry has been received yet.
        """
        battery_tel = self._get_battery_tel()
        if battery_tel is None:
            return None
        return self._packs_from_tel(battery_tel)

    def get_state_of_charge(self) -> Optional[float]:
        """Get the state of charge for the drone as a whole.

        On drones with two battery packs (e.g. the X7) this is currently the lowest level of the
        packs, so a depleted pack is not masked by a full one. Use `get_packs()` to read the level
        of each pack.

        Returns:
            Current state of charge of the drone battery (0..1).
        """
        packs = self.get_packs()
        if packs is None:
            return None
        return min(pack.level for pack in packs)

    state_of_charge = deprecated_property("get_state_of_charge")

    def get_voltage(self) -> Optional[float]:
        """Get the battery voltage for the drone as a whole.

        On drones with two battery packs (e.g. the X7) this is currently the lowest voltage of the
        packs. Use `get_packs()` to read the voltage of each pack.

        Returns:
            Current battery voltage (V).
        """
        packs = self.get_packs()
        if packs is None:
            return None
        return min(pack.voltage for pack in packs)

    def get_temperature(self) -> Optional[float]:
        """Get the battery temperature for the drone as a whole.

        On drones with two battery packs (e.g. the X7) this is currently the highest temperature
        of the packs. Use `get_packs()` to read the temperature of each pack.

        Returns:
            Current battery temperature (°C).
        """
        packs = self.get_packs()
        if packs is None:
            return None
        return max(pack.temperature for pack in packs)

    def get_details(self) -> Optional[List[blueye.protocol.BatteryBQ40Z50]]:
        """Get the detailed battery management system information for each physical battery pack.

        Returns:
            A list with one `blueye.protocol.BatteryBQ40Z50` message per pack in slot order, with
            cell voltages, cell temperatures, current, capacities, time to empty, cycle count,
            status flags and more. Single battery drones return a list with one entry, the X7
            returns two entries while a pack is present in the second slot. None if no detailed
            battery telemetry has been received yet.
        """
        details_tel = self._parent_drone.telemetry.get(blueye.protocol.BatteryBQ40Z50Tel)
        if details_tel is None:
            return None
        return self._packs_from_tel(details_tel)
