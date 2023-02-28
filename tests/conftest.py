from unittest.mock import Mock

import pytest

import blueye.sdk
from blueye.sdk import Drone


@pytest.fixture(scope="class")
def real_drone():
    """Fixture that autoconnects to a drone

    Used for integration tests with physical hardware.
    """
    return Drone()


@pytest.fixture
def mocked_requests(requests_mock):
    import json

    dummy_drone_info = {
        "commit_id_csys": "299238949a",
        "features": "lasers,harpoon",
        "hardware_id": "ea9ac92e1817a1d4",
        "manufacturer": "Blueye Robotics",
        "model_description": "Blueye Pioneer Underwater Drone",
        "model_name": "Blueye Pioneer",
        "model_url": "https://www.blueyerobotics.com",
        "operating_system": "blunux",
        "serial_number": "BYEDP123456",
        "sw_version": "1.4.7-warrior-master",
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
def mocked_TcpClient(mocker):
    """Fixture for mocking the TcpClient from blueye.protocol

    Note: This mock is passed create=True, which has the potential to be dangerous since it would
    allow you to test against methods that don't exist on the actual class. Due to the way methods
    are added to TcpClient (they are instantiated on runtime, depending on which version of the
    protocol is requested) mocking the class in the usual way would be quite cumbersome.
    """
    return mocker.patch("blueye.sdk.drone.TcpClient", create=True)


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
    mocked_TcpClient,
    mocked_requests,
    mocked_ctrl_client,
    mocked_watchdog_publisher,
    mocked_req_rep_client,
):
    drone = blueye.sdk.Drone(autoConnect=False)
    drone._wait_for_udp_communication = Mock()
    drone.connect()
    if hasattr(request, "param"):
        drone.software_version_short = request.param
    return drone


@pytest.fixture
def mocked_slave_drone(mocker, mocked_TcpClient, mocked_requests):
    drone = blueye.sdk.Drone(autoConnect=False, slaveModeEnabled=True)
    drone.connect()
    return drone
