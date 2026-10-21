import json

import pytest
import requests

from blueye.sdk.cv_models import CvModel, CvModels

BASE = "http://192.168.1.101/api/cv-models"

MODEL_ENTRY = {
    "name": "Cod Detector",
    "directory": "cod-detector",
    "type": "detection",
    "output_format": "yolov8_flat",
    "size_bytes": 10485760,
    "labels": ["cod", "salmon"],
    "enabled": False,
    "runtime": {"device": "tensorrt-dla0", "hz": 10, "enabled": False},
}


@pytest.fixture
def cv_models(mocker):
    """A CvModels client on a drone that is not connected, which is all the HTTP calls need."""
    from blueye.sdk.drone import _NoConnectionClient

    drone = mocker.Mock()
    drone._ip = "192.168.1.101"
    drone.connected = False
    drone._ctrl_client = _NoConnectionClient()
    return CvModels(drone)


@pytest.fixture
def connected_cv_models(mocker):
    """A CvModels client on a connected drone, with a mocked control client."""
    drone = mocker.Mock()
    drone._ip = "192.168.1.101"
    drone.connected = True
    return CvModels(drone)


class TestList:
    def test_list_parses_entries(self, cv_models, requests_mock):
        requests_mock.get(f"{BASE}/", json=[MODEL_ENTRY])
        models = cv_models.list()
        assert len(models) == 1
        model = models[0]
        assert model.name == "Cod Detector"
        assert model.directory == "cod-detector"
        assert model.type == "detection"
        assert model.output_format == "yolov8_flat"
        assert model.size_bytes == 10485760
        assert model.labels == ["cod", "salmon"]
        assert model.enabled is False
        assert model.raw["runtime"]["device"] == "tensorrt-dla0"

    def test_empty_list(self, cv_models, requests_mock):
        requests_mock.get(f"{BASE}/", json=[])
        assert cv_models.list() == []

    def test_list_sorted_by_directory(self, cv_models, requests_mock):
        requests_mock.get(
            f"{BASE}/",
            json=[
                {"name": "B", "directory": "b-model"},
                {"name": "A", "directory": "a-model"},
            ],
        )
        models = cv_models.list()
        assert [model.directory for model in models] == ["a-model", "b-model"]

    def test_missing_optional_fields_defaulted(self):
        model = CvModel.from_json({"name": "x", "directory": "x"})
        assert model.type == "unknown"
        assert model.size_bytes == 0
        assert model.labels == []
        assert model.enabled is False


class TestUpload:
    def test_upload_sends_multipart_file_field(self, cv_models, requests_mock, tmp_path):
        package = tmp_path / "pkg.zip"
        package.write_bytes(b"zip-bytes")
        requests_mock.post(f"{BASE}/upload", json=MODEL_ENTRY)

        model = cv_models.upload(package)

        assert model.directory == "cod-detector"
        request = requests_mock.last_request
        assert 'name="file"' in request.text
        assert "zip-bytes" in request.text

    def test_upload_rejection_surfaces_server_reason(self, cv_models, requests_mock, tmp_path):
        package = tmp_path / "pkg.zip"
        package.write_bytes(b"not really a zip")
        requests_mock.post(
            f"{BASE}/upload",
            status_code=400,
            text="Uploaded file is not a valid zip archive.",
        )
        with pytest.raises(requests.exceptions.HTTPError, match="not a valid zip archive"):
            cv_models.upload(package)


class TestDelete:
    def test_delete(self, cv_models, requests_mock):
        requests_mock.delete(f"{BASE}/cod-detector", json={"success": True, "message": "deleted"})
        cv_models.delete("cod-detector")
        assert requests_mock.called

    def test_delete_unknown_raises_with_reason(self, cv_models, requests_mock):
        requests_mock.delete(f"{BASE}/nope", status_code=404, text="Model 'nope' not found.")
        with pytest.raises(requests.exceptions.HTTPError, match="not found"):
            cv_models.delete("nope")


class TestDownload:
    def test_download_uses_content_disposition_name(self, cv_models, requests_mock, tmp_path):
        requests_mock.get(
            f"{BASE}/cod-detector/download",
            content=b"zip-bytes",
            headers={"Content-Disposition": 'attachment; filename="cod-detector.zip"'},
        )
        output = cv_models.download("cod-detector", output_path=tmp_path)
        assert output == tmp_path / "cod-detector.zip"
        assert output.read_bytes() == b"zip-bytes"

    def test_download_ignores_extra_disposition_parameters(
        self, cv_models, requests_mock, tmp_path
    ):
        requests_mock.get(
            f"{BASE}/cod-detector/download",
            content=b"zip-bytes",
            headers={"Content-Disposition": 'attachment; filename="cod-detector.zip"; foo="bar"'},
        )
        output = cv_models.download("cod-detector", output_path=tmp_path)
        assert output == tmp_path / "cod-detector.zip"

    def test_download_fallback_name_and_explicit_path(self, cv_models, requests_mock, tmp_path):
        requests_mock.get(f"{BASE}/cod-detector/download", content=b"zip-bytes")
        output = cv_models.download("cod-detector", output_path=tmp_path / "my.zip")
        assert output == tmp_path / "my.zip"
        assert output.read_bytes() == b"zip-bytes"


class TestConfiguration:
    def test_set_enabled_payload(self, cv_models, requests_mock):
        requests_mock.patch(f"{BASE}/cod-detector/enabled", json={"success": True})
        cv_models.set_enabled("cod-detector", True)
        assert json.loads(requests_mock.last_request.text) == {"enabled": True}

    def test_set_device_payload(self, cv_models, requests_mock):
        requests_mock.patch(f"{BASE}/cod-detector/device", json={"success": True})
        cv_models.set_device("cod-detector", "tensorrt-dla1")
        assert json.loads(requests_mock.last_request.text) == {"device": "tensorrt-dla1"}

    def test_set_device_rejection_surfaces_reason(self, cv_models, requests_mock):
        requests_mock.patch(
            f"{BASE}/cod-detector/device",
            status_code=400,
            text="'device' must be one of: cuda, tensorrt, tensorrt-dla0, tensorrt-dla1.",
        )
        with pytest.raises(requests.exceptions.HTTPError, match="must be one of"):
            cv_models.set_device("cod-detector", "gameboy")

    def test_set_hz_payload(self, cv_models, requests_mock):
        requests_mock.patch(f"{BASE}/cod-detector/hz", json={"success": True})
        cv_models.set_hz("cod-detector", 10)
        assert json.loads(requests_mock.last_request.text) == {"hz": 10}


class TestWarmupAndRescan:
    def test_warmup(self, cv_models, requests_mock):
        requests_mock.post(f"{BASE}/cod-detector/warmup", json={"success": True})
        cv_models.warmup("cod-detector")
        assert requests_mock.called

    def test_warmup_unavailable_off_drone(self, cv_models, requests_mock):
        requests_mock.post(
            f"{BASE}/cod-detector/warmup",
            status_code=503,
            json={"success": False, "message": "Warmup is not available on this device."},
        )
        with pytest.raises(requests.exceptions.HTTPError, match="503"):
            cv_models.warmup("cod-detector")

    def test_rescan_sends_the_control_message(self, connected_cv_models):
        connected_cv_models.rescan()
        connected_cv_models._parent_drone._ctrl_client.rescan_cv_models.assert_called_once_with()

    def test_rescan_needs_a_connection(self, cv_models):
        with pytest.raises(ConnectionError):
            cv_models.rescan()

    def test_rescan_timeout_is_deprecated_and_ignored(self, connected_cv_models):
        with pytest.warns(DeprecationWarning, match="timeout"):
            connected_cv_models.rescan(timeout=5)
        connected_cv_models._parent_drone._ctrl_client.rescan_cv_models.assert_called_once_with()


# (method, args, HTTP verb, URL path) for the changes the drone only picks up after a rescan
CHANGES = [
    ("delete", ("cod-detector",), "delete", "/cod-detector"),
    ("set_enabled", ("cod-detector", True), "patch", "/cod-detector/enabled"),
    ("set_device", ("cod-detector", "cuda"), "patch", "/cod-detector/device"),
    ("set_hz", ("cod-detector", 10), "patch", "/cod-detector/hz"),
]


class TestAutomaticRescan:
    @pytest.mark.parametrize("method, args, verb, path", CHANGES)
    def test_changes_rescan_while_connected(
        self, connected_cv_models, requests_mock, method, args, verb, path
    ):
        getattr(requests_mock, verb)(f"{BASE}{path}", json={"success": True})
        getattr(connected_cv_models, method)(*args)
        connected_cv_models._parent_drone._ctrl_client.rescan_cv_models.assert_called_once_with()

    def test_upload_rescans_while_connected(self, connected_cv_models, requests_mock, tmp_path):
        requests_mock.post(f"{BASE}/upload", json=MODEL_ENTRY)
        package = tmp_path / "pkg.zip"
        package.write_bytes(b"zip")
        connected_cv_models.upload(package)
        connected_cv_models._parent_drone._ctrl_client.rescan_cv_models.assert_called_once_with()

    @pytest.mark.parametrize("method, args, verb, path", CHANGES)
    def test_changes_warn_when_not_connected(
        self, cv_models, requests_mock, caplog, method, args, verb, path
    ):
        getattr(requests_mock, verb)(f"{BASE}{path}", json={"success": True})
        with caplog.at_level("WARNING", logger="blueye.sdk.cv_models"):
            getattr(cv_models, method)(*args)
        assert "not been asked to rescan" in caplog.text

    def test_rescan_is_not_sent_when_the_change_fails(self, connected_cv_models, requests_mock):
        requests_mock.patch(f"{BASE}/cod-detector/hz", status_code=400, text="bad rate")
        with pytest.raises(requests.exceptions.HTTPError):
            connected_cv_models.set_hz("cod-detector", 10)
        connected_cv_models._parent_drone._ctrl_client.rescan_cv_models.assert_not_called()


def test_drone_has_cv_models_feature(mocker):
    import blueye.sdk

    mocker.patch("blueye.sdk.drone.CtrlClient", autospec=True)
    mocker.patch("blueye.sdk.drone.TelemetryClient", autospec=True)
    mocker.patch("blueye.sdk.drone.WatchdogPublisher", autospec=True)
    mocker.patch("blueye.sdk.drone.ReqRepClient", autospec=True)
    drone = blueye.sdk.Drone(auto_connect=False)
    assert isinstance(drone.cv_models, CvModels)
    assert drone.cv_models._parent_drone is drone
