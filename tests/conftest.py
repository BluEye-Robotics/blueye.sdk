import blueye.protocol as bp
import pytest

import blueye.sdk


@pytest.fixture(scope="class")
def real_drone():
    """Fixture that autoconnects to a drone

    Used for integration tests with physical hardware.
    """
    return blueye.sdk.Drone()


@pytest.fixture
def mocked_requests(requests_mock):
    import json

    dummy_drone_info = {
        "commit_id_csys": "299238949a",
        "features": "lasers,harpoon",
        "hardware_id": "ea9ac92e1817a1d4",
        "manufacturer": "Blueye Robotics",
        "model_description": "Blueye X3 Underwater Drone",
        "model_name": "Blueye X3",
        "model_url": "https://www.blueyerobotics.com",
        "operating_system": "blunux",
        "serial_number": "BYEDP230000",
        "sw_version": "3.2.62-honister-master",
    }
    requests_mock.get(
        "http://192.168.1.101/diagnostics/drone_info",
        content=json.dumps(dummy_drone_info).encode(),
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
def mocked_ctrl_client(mocker):
    return mocker.patch("blueye.sdk.drone.CtrlClient", autospec=True)


@pytest.fixture
def mocked_telemetry_client(mocker):
    return mocker.patch("blueye.sdk.drone.TelemetryClient", autospec=True)


@pytest.fixture
def mocked_watchdog_publisher(mocker):
    return mocker.patch("blueye.sdk.drone.WatchdogPublisher", autospec=True)


@pytest.fixture
def mocked_req_rep_client(mocker):
    return mocker.patch("blueye.sdk.drone.ReqRepClient", autospec=True)


@pytest.fixture
def mocked_drone(
    request,
    mocker,
    mocked_requests,
    mocked_ctrl_client,
    mocked_watchdog_publisher,
    mocked_req_rep_client,
):
    drone = blueye.sdk.Drone()
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
    if hasattr(request, "param"):
        drone.software_version_short = request.param
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
