import time

import blueye.protocol as bp
import pytest

import blueye.sdk


@pytest.fixture(scope="class")
def real_drone():
    """Fixture that autoconnects to a drone

    Used for integration tests with physical hardware.
    """
    return blueye.sdk.Drone()


@pytest.fixture(scope="class")
def drone_model(real_drone) -> bp.Model:
    """Fixture that reports the model of the connected drone

    Used to skip integration tests for camera parameters the connected hardware does not
    support. Returns MODEL_UNSPECIFIED if no drone info is received, which is also what
    drones older than the introduction of the model field report.
    """
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        model = real_drone.get_model()
        if model is not None:
            return model
        time.sleep(0.1)
    return bp.Model.MODEL_UNSPECIFIED


# The HTTP drone_info reply of an X3 on Blunux 3.2, which the plain mocked_drone is built from.
DRONE_INFO_X3 = {
    "commit_id_csys": "299238949a",
    "features": "tilt",
    "hardware_id": "ea9ac92e1817a1d4",
    "manufacturer": "Blueye Robotics",
    "model_description": "Blueye X3 Underwater Drone",
    "model_name": "Blueye X3",
    "model_url": "https://www.blueyerobotics.com",
    "operating_system": "blunux",
    "serial_number": "BYEDP230000",
    "sw_version": "3.2.62-honister-master",
}

# The reply of an X7 on Blunux 5.0. Newer drones report the model name without the "Blueye"
# prefix and only the gpdrone feature, the rest is read from DroneInfoTel.
DRONE_INFO_X7 = {
    "features": "gpdrone",
    "hardware_id": "1d4a7e8f2c9b3a60",
    "manufacturer": "Blueye Robotics",
    "model_description": "Blueye X7 Underwater Drone",
    "model_name": "X7",
    "model_url": "https://www.blueyerobotics.com",
    "operating_system": "blunux",
    "serial_number": "BYEDP260000",
    "sw_version": "5.0.0-walnascar-master",
}


def _mock_drone_http(requests_mock, drone_info: dict):
    import json

    requests_mock.get(
        "http://192.168.1.101/diagnostics/drone_info",
        content=json.dumps(drone_info).encode(),
    )

    dummy_logs = json.dumps(
        [
            {
                "maxdepth": 1000,
                "name": "log1.csv",
                "timestamp": "2019-01-01T00:00:00.000000",
                "binsize": 1024,
            },
            {
                "maxdepth": 2000,
                "name": "log2.csv",
                "timestamp": "2019-01-02T00:00:00.000000",
                "binsize": 2048,
            },
        ]
    )
    requests_mock.get(f"http://192.168.1.101/logcsv", content=str.encode(dummy_logs))


@pytest.fixture
def mocked_requests(requests_mock):
    _mock_drone_http(requests_mock, DRONE_INFO_X3)


@pytest.fixture
def mocked_requests_x7(requests_mock):
    _mock_drone_http(requests_mock, DRONE_INFO_X7)


@pytest.fixture
def mocked_ctrl_client(mocker):
    return mocker.patch("blueye.sdk.drone.CtrlClient", autospec=True)


@pytest.fixture
def mocked_telemetry_client(mocker):
    """Patch the telemetry subscriber so unit tests never read telemetry off the network.

    Without this the drone built by `mocked_drone` opens a real ZMQ subscriber against the
    drone IP, and any drone on the same network fills its state within a few hundred
    milliseconds. That makes every "returns None when no telemetry has been received" test
    fail at random, depending on which one happens to run late enough to receive something.

    The mock keeps a real dict for `_state` and looks messages up in it, raising KeyError for
    the ones that are missing, so tests can keep seeding telemetry by assigning to
    `drone._telemetry_watcher._state[SomeTel]`.
    """
    patched = mocker.patch("blueye.sdk.drone.TelemetryClient", autospec=True)
    instance = patched.return_value
    instance._state = {}
    # Read the attribute on every call rather than closing over the dict, because the real
    # get() looks up self._state and several tests rebind _state to a fresh dict.
    instance.get.side_effect = lambda key: instance._state[key]
    return patched


@pytest.fixture
def mocked_watchdog_publisher(mocker):
    return mocker.patch("blueye.sdk.drone.WatchdogPublisher", autospec=True)


@pytest.fixture
def mocked_req_rep_client(mocker):
    return mocker.patch("blueye.sdk.drone.ReqRepClient", autospec=True)


def _mock_drone_replies(drone: blueye.sdk.Drone):
    """Give the mocked request-reply client the answers connect() and the overlay need."""
    drone._req_rep_client.get_overlay_parameters.return_value = bp.OverlayParameters(
        temperature_enabled=False,
        depth_enabled=False,
        heading_enabled=False,
        tilt_enabled=False,
        thickness_enabled=False,
        date_enabled=False,
        distance_enabled=False,
        altitude_enabled=False,
        cp_probe_enabled=False,
        medusa_enabled=False,
        drone_location_enabled=False,
        logo_type=bp.LogoType.LOGO_TYPE_NONE,
        depth_unit=bp.DepthUnit.DEPTH_UNIT_METERS,
        temperature_unit=bp.TemperatureUnit.TEMPERATURE_UNIT_CELSIUS,
        thickness_unit=bp.ThicknessUnit.THICKNESS_UNIT_MILLIMETERS,
        timezone_offset=60,
        margin_width=30,
        margin_height=15,
        font_size=bp.FontSize.FONT_SIZE_PX25,
        title="",
        subtitle="",
        date_format="%m/%d/%Y %I:%M:%S %p",
        shading=0,
    )
    drone._req_rep_client.connect_client.return_value = bp.ConnectClientRep(
        client_id=1, client_id_in_control=1
    )
    # A telemetry message the drone has not published comes back empty, see Telemetry.get
    drone._req_rep_client.get_telemetry_msg.return_value = bp.GetTelemetryRep()


def _seed_telemetry(state: dict, msg):
    """Store a telemetry message in a mocked telemetry client's state, as if it had arrived."""
    state[type(msg)] = type(msg).serialize(msg)


@pytest.fixture
def mocked_drone(
    request,
    mocker,
    mocked_requests,
    mocked_ctrl_client,
    mocked_telemetry_client,
    mocked_watchdog_publisher,
    mocked_req_rep_client,
):
    drone = blueye.sdk.Drone()
    _mock_drone_replies(drone)
    if hasattr(request, "param"):
        drone.software_version_short = request.param
    return drone


def _guest_port(number: bp.GuestPortNumber, *device_ids: bp.GuestPortDeviceID):
    port = bp.GuestPortConnectorInfo(guest_port_number=number)
    if device_ids:
        port.device_list = bp.GuestPortDeviceList(
            devices=[bp.GuestPortDevice(device_id=device_id) for device_id in device_ids]
        )
    else:
        port.error = bp.GuestPortError.GUEST_PORT_ERROR_NOT_CONNECTED
    return port


@pytest.fixture
def mocked_drone_x7(
    mocker,
    mocked_requests_x7,
    mocked_ctrl_client,
    mocked_telemetry_client,
    mocked_watchdog_publisher,
    mocked_req_rep_client,
):
    """A connected X7 on Blunux 5.0.0.

    DroneInfoTel reports MODEL_X7, two batteries in parallel and six guest ports: a GNSS
    receiver on port 1, a DVL on port 2, a light on port 4 and the rest not connected. BatteryTel
    carries both packs. Both messages are in place before the drone connects, so connect()
    discovers the peripherals from the drone info the way it does on a real drone.

    On Blunux 3.3 and newer a telemetry message that has not been received is requested from
    the drone, so the request client answers with an empty reply for the messages that are not
    seeded here, as a drone that has not published them would.
    """
    mocked_req_rep_client.return_value.get_telemetry_msg.return_value = bp.GetTelemetryRep()
    state = mocked_telemetry_client.return_value._state
    _seed_telemetry(
        state,
        bp.DroneInfoTel(
            drone_info=bp.DroneInfo(
                blunux_version="5.0.0",
                serial_number=DRONE_INFO_X7["serial_number"].encode(),
                hardware_id=DRONE_INFO_X7["hardware_id"].encode(),
                model=bp.Model.MODEL_X7,
                power_source=bp.PowerSource.POWER_SOURCE_PARALLEL_BATTERIES,
                gp=bp.GuestPortInfo(
                    gp1=_guest_port(
                        bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_1,
                        bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEYE_GNSS_DEVICE,
                    ),
                    gp2=_guest_port(
                        bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_2,
                        bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_WATERLINKED_DVL_A50,
                    ),
                    gp3=_guest_port(bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_3),
                    gp4=_guest_port(
                        bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_4,
                        bp.GuestPortDeviceID.GUEST_PORT_DEVICE_ID_BLUEYE_LIGHT,
                    ),
                    gp5=_guest_port(bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_5),
                    gp6=_guest_port(bp.GuestPortNumber.GUEST_PORT_NUMBER_PORT_6),
                ),
            )
        ),
    )
    _seed_telemetry(
        state,
        bp.BatteryTel(
            battery=bp.Battery(voltage=15.8, level=0.8, temperature=24.0),
            second_battery=bp.Battery(voltage=15.6, level=0.7, temperature=25.0),
        ),
    )
    drone = blueye.sdk.Drone()
    _mock_drone_replies(drone)
    return drone


@pytest.fixture
def mocked_drone_not_connected(
    mocker,
    mocked_requests,
    mocked_ctrl_client,
    mocked_watchdog_publisher,
    mocked_req_rep_client,
):
    return blueye.sdk.Drone(auto_connect=False)
