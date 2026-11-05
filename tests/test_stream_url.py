"""Camera.get_stream_url: the stream URL from drone_info `services`, with the connected host."""

import pytest

from blueye.sdk.camera import Camera

DRONE_INFO_URL = "http://192.168.1.101/diagnostics/drone_info"

# As reported by an X3 Ultra on Blunux 5.2 with a guest port camera attached
SERVICES = [
    {"type": "videostream", "options": {"url": "rtsp://192.168.1.101:8554/test", "primary": True}},
    {
        "type": "videostream",
        "options": {"url": "rtsp://192.168.1.101:8555/guestport_cam", "primary": False},
    },
    {"type": "tilt", "options": {}},
]


@pytest.fixture
def guestport_camera(mocked_drone):
    return Camera(mocked_drone, is_guestport_camera=True)


def test_main_camera_url_comes_from_services(mocked_drone):
    mocked_drone._services = [
        {
            "type": "videostream",
            "options": {"url": "rtsp://192.168.1.101:9554/cam", "primary": True},
        }
    ]
    assert mocked_drone.camera.get_stream_url() == "rtsp://192.168.1.101:9554/cam"


def test_guestport_camera_uses_the_non_primary_stream(mocked_drone, guestport_camera):
    mocked_drone._services = SERVICES
    assert mocked_drone.camera.get_stream_url() == "rtsp://192.168.1.101:8554/test"
    assert guestport_camera.get_stream_url() == "rtsp://192.168.1.101:8555/guestport_cam"


def test_the_advertised_host_is_replaced_by_the_connected_address(mocked_drone, guestport_camera):
    mocked_drone._services = SERVICES
    mocked_drone._ip = "10.0.0.7"
    assert mocked_drone.camera.get_stream_url() == "rtsp://10.0.0.7:8554/test"
    assert guestport_camera.get_stream_url() == "rtsp://10.0.0.7:8555/guestport_cam"


def test_an_ipv6_address_is_bracketed(mocked_drone):
    mocked_drone._services = SERVICES
    mocked_drone._ip = "fd00::7"
    assert mocked_drone.camera.get_stream_url() == "rtsp://[fd00::7]:8554/test"


@pytest.mark.parametrize("services", [None, []])
def test_without_a_stream_list_the_defaults_are_used(mocked_drone, guestport_camera, services):
    mocked_drone._services = services
    mocked_drone._ip = "10.0.0.7"
    assert mocked_drone.camera.get_stream_url() == "rtsp://10.0.0.7:8554/test"
    assert guestport_camera.get_stream_url() == "rtsp://10.0.0.7:8555/guestport_cam"


def test_a_guestport_camera_missing_from_the_list_gets_its_default(mocked_drone, guestport_camera):
    mocked_drone._services = SERVICES[:1]
    assert guestport_camera.get_stream_url() == "rtsp://192.168.1.101:8555/guestport_cam"


@pytest.mark.parametrize(
    "entry",
    [
        "not a dict",
        {"type": "videostream"},
        {"type": "videostream", "options": "no dict"},
        {"type": "videostream", "options": {"primary": True}},
        {"type": "videostream", "options": {"url": 554, "primary": True}},
        {"type": "videostream", "options": {"url": "http://192.168.1.101/x", "primary": True}},
        {
            "type": "videostream",
            "options": {"url": "rtsp://192.168.1.101:99999/x", "primary": True},
        },
        {"type": "videostream", "options": {"url": "rtsp://192.168.1.101:8554", "primary": True}},
        {"type": "audiostream", "options": {"url": "rtsp://192.168.1.101:1/x", "primary": True}},
        {"type": "videostream", "options": {"url": "rtsp://[bad/test", "primary": True}},
    ],
)
def test_malformed_entries_are_skipped(mocked_drone, entry):
    mocked_drone._services = [entry]
    assert mocked_drone.camera.get_stream_url() == "rtsp://192.168.1.101:8554/test"


def test_a_malformed_entry_does_not_hide_a_valid_one(mocked_drone):
    mocked_drone._services = [
        {"type": "videostream", "options": {"url": "rtsp://[bad/test", "primary": True}},
        {
            "type": "videostream",
            "options": {"url": "rtsp://192.168.1.101:9554/cam", "primary": True},
        },
    ]
    assert mocked_drone.camera.get_stream_url() == "rtsp://192.168.1.101:9554/cam"


def test_a_url_without_a_port_keeps_none(mocked_drone):
    mocked_drone._services = [
        {"type": "videostream", "options": {"url": "rtsp://192.168.1.101/live", "primary": True}}
    ]
    assert mocked_drone.camera.get_stream_url() == "rtsp://192.168.1.101/live"


def test_connect_reads_the_services_from_drone_info(mocked_drone, requests_mock):
    from tests.conftest import DRONE_INFO_X3

    requests_mock.get(DRONE_INFO_URL, json={**DRONE_INFO_X3, "services": SERVICES})
    mocked_drone._update_drone_info()
    assert mocked_drone._services == SERVICES


@pytest.mark.parametrize("services", ["", None, {"url": "x"}])
def test_a_drone_info_without_a_service_list_stores_none(mocked_drone, requests_mock, services):
    from tests.conftest import DRONE_INFO_X3

    # A drone that could not read its hardware in time answers with services set to ""
    requests_mock.get(DRONE_INFO_URL, json={**DRONE_INFO_X3, "services": services})
    mocked_drone._update_drone_info()
    assert mocked_drone._services is None


def test_a_drone_that_never_connected_gets_the_default(mocked_drone_not_connected):
    assert mocked_drone_not_connected.camera.get_stream_url() == "rtsp://192.168.1.101:8554/test"
