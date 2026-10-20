"""Tests for the battery module.

Single battery drones fill only `battery` in the telemetry messages. The X7 runs two packs in
parallel and also fills `second_battery`, which the drone does not aggregate. The getters reduce
the packs like the Blueye app does: lowest level, lowest voltage and highest temperature.
"""

import blueye.protocol as bp
import pytest

SINGLE_PACK = {"level": 0.8, "voltage": 15.3, "temperature": 24.0}
WEAK_PACK = {"level": 0.15, "voltage": 13.1, "temperature": 31.5}


def _seed(drone, tel):
    drone._telemetry_watcher._state[type(tel)] = type(tel).serialize(tel)


@pytest.fixture
def single_battery_drone(mocked_drone):
    _seed(mocked_drone, bp.BatteryTel(battery=SINGLE_PACK))
    _seed(mocked_drone, bp.BatteryBQ40Z50Tel(battery={"cycle_count": 12}))
    return mocked_drone


@pytest.fixture
def dual_battery_drone(mocked_drone):
    _seed(mocked_drone, bp.BatteryTel(battery=SINGLE_PACK, second_battery=WEAK_PACK))
    _seed(
        mocked_drone,
        bp.BatteryBQ40Z50Tel(battery={"cycle_count": 12}, second_battery={"cycle_count": 34}),
    )
    return mocked_drone


class TestNoTelemetry:
    @pytest.mark.parametrize(
        "getter",
        [
            "has_second_battery",
            "get_packs",
            "get_state_of_charge",
            "get_voltage",
            "get_temperature",
            "get_details",
        ],
    )
    def test_getters_return_none_before_telemetry_arrives(self, mocked_drone, getter):
        assert getattr(mocked_drone.battery, getter)() is None


class TestSingleBattery:
    def test_has_second_battery(self, single_battery_drone):
        assert single_battery_drone.battery.has_second_battery() is False

    def test_get_packs(self, single_battery_drone):
        packs = single_battery_drone.battery.get_packs()
        assert len(packs) == 1
        assert packs[0].level == pytest.approx(SINGLE_PACK["level"])

    def test_state_of_charge(self, single_battery_drone):
        assert single_battery_drone.battery.get_state_of_charge() == pytest.approx(
            SINGLE_PACK["level"]
        )

    def test_voltage(self, single_battery_drone):
        assert single_battery_drone.battery.get_voltage() == pytest.approx(SINGLE_PACK["voltage"])

    def test_temperature(self, single_battery_drone):
        assert single_battery_drone.battery.get_temperature() == pytest.approx(
            SINGLE_PACK["temperature"]
        )

    def test_get_details(self, single_battery_drone):
        details = single_battery_drone.battery.get_details()
        assert len(details) == 1
        assert details[0].cycle_count == 12


class TestDualBattery:
    def test_has_second_battery(self, dual_battery_drone):
        assert dual_battery_drone.battery.has_second_battery() is True

    def test_get_packs(self, dual_battery_drone):
        packs = dual_battery_drone.battery.get_packs()
        assert len(packs) == 2
        assert packs[0].level == pytest.approx(SINGLE_PACK["level"])
        assert packs[1].level == pytest.approx(WEAK_PACK["level"])

    def test_state_of_charge_is_lowest_pack(self, dual_battery_drone):
        assert dual_battery_drone.battery.get_state_of_charge() == pytest.approx(WEAK_PACK["level"])

    def test_voltage_is_lowest_pack(self, dual_battery_drone):
        assert dual_battery_drone.battery.get_voltage() == pytest.approx(WEAK_PACK["voltage"])

    def test_temperature_is_highest_pack(self, dual_battery_drone):
        assert dual_battery_drone.battery.get_temperature() == pytest.approx(
            WEAK_PACK["temperature"]
        )

    def test_get_details(self, dual_battery_drone):
        details = dual_battery_drone.battery.get_details()
        assert len(details) == 2
        assert details[0].cycle_count == 12
        assert details[1].cycle_count == 34

    def test_second_pack_set_to_zero_is_still_reported(self, mocked_drone):
        # A second pack that reports all zeros is a present pack, not a missing one, and must
        # drive the aggregated state of charge down to zero.
        _seed(
            mocked_drone,
            bp.BatteryTel(battery=SINGLE_PACK, second_battery={"level": 0.0}),
        )
        assert mocked_drone.battery.has_second_battery() is True
        assert mocked_drone.battery.get_state_of_charge() == pytest.approx(0.0)
