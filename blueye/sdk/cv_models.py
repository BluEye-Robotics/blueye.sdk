"""Manage the computer vision model packages installed on the drone.

The Blueye X3 Ultra runs CV model packages (an ONNX model plus a
`model_meta.json`, see the "Bundling CV models" documentation). This module wraps the
drone's HTTP API for managing those packages: listing, uploading, deleting,
downloading, configuring (autolaunch/device/rate), and pre-building inference engines.

The API is plain HTTP and independent of the drone's control connection, so these
methods work on a `Drone(auto_connect=False)` instance as well — no control over the
drone is taken.
"""

from __future__ import annotations

import logging
import re
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    import blueye.sdk

logger = logging.getLogger(__name__)

#: Execution providers accepted by the drone's `set_device` endpoint.
VALID_DEVICES = ("cuda", "tensorrt", "tensorrt-dla0", "tensorrt-dla1")

#: Inference rates (Hz) accepted by the drone's `set_hz` endpoint; 0 means unlimited.
VALID_HZ = (0, 5, 10, 15)


@dataclass(frozen=True)
class CvModel:
    """One CV model package installed on the drone.

    Attributes:
        name: The human-readable model name from its model_meta.json.
        directory: The package's directory slug on the drone — this is the identifier
            the other methods take as `name`.
        type: "detection", "sot", or "unknown".
        output_format: The decoder format (e.g. "yolov8_flat").
        size_bytes: Size of the model weights file.
        labels: Class labels.
        enabled: Whether the model autolaunches on the drone (runtime.enabled).
        raw: The verbatim API entry, including the optional preprocessing/detection/
            sot/tracking/runtime blocks when present.
    """

    name: str
    directory: str
    type: str
    output_format: str
    size_bytes: int
    labels: list[str]
    enabled: bool
    raw: dict = field(repr=False)

    @classmethod
    def from_json(cls, entry: dict) -> CvModel:
        """Build a CvModel from one entry of the drone's API response."""
        return cls(
            name=entry.get("name", ""),
            directory=entry.get("directory", ""),
            type=entry.get("type", "unknown"),
            output_format=entry.get("output_format", ""),
            size_bytes=int(entry.get("size_bytes", 0)),
            labels=list(entry.get("labels", [])),
            enabled=bool(entry.get("enabled", False)),
            raw=entry,
        )


class CvModels:
    """CV model package management on the drone.

    Accessed through `drone.cv_models`, e.g.::

        drone = blueye.sdk.Drone(auto_connect=False)
        for model in drone.cv_models.list():
            print(model.name, model.enabled)

    All methods raise `requests.exceptions.ConnectionError`/`ConnectTimeout` when the
    drone is unreachable, and `requests.exceptions.HTTPError` (with the drone's error
    message included) when the drone rejects a request.

    The listing and the changes go over HTTP and need no connection. The drone only picks
    up a change after a rescan, which is a control message, so
    [`upload`][blueye.sdk.cv_models.CvModels.upload],
    [`delete`][blueye.sdk.cv_models.CvModels.delete] and the `set_*` methods send one when
    the drone is connected (an observer connection is enough) and log a warning when it is
    not. [`rescan`][blueye.sdk.cv_models.CvModels.rescan] sends one on its own.
    """

    def __init__(self, parent_drone: "blueye.sdk.Drone"):
        self._parent_drone = parent_drone

    @property
    def _base_url(self) -> str:
        return f"http://{self._parent_drone._ip}/api/cv-models"

    @staticmethod
    def _check(response: requests.Response) -> requests.Response:
        """Raise HTTPError for non-2xx responses, keeping the drone's reason.

        The drone's API returns its error reasons as text/plain bodies, which a bare
        `raise_for_status()` would discard.
        """
        if not response.ok:
            detail = response.text.strip()
            message = f"{response.status_code} error for {response.url}"
            if detail:
                message += f": {detail}"
            raise requests.exceptions.HTTPError(message, response=response)
        return response

    def list(self, timeout: float = 5) -> list[CvModel]:
        """List the model packages installed on the drone.

        Args:
            timeout: Request timeout in seconds.

        Returns:
            One CvModel per installed package, sorted by directory name.
        """
        response = self._check(requests.get(f"{self._base_url}/", timeout=timeout))
        models = [CvModel.from_json(entry) for entry in response.json()]
        return sorted(models, key=lambda model: model.directory)

    def upload(self, package: Path | str, timeout: float = 60) -> CvModel:
        """Upload a model package zip to the drone.

        The drone validates the archive (it must contain a valid model_meta.json and
        the model file it references) and installs it into a directory named after
        the slugified model name — an existing package with the same slug is
        replaced.

        Args:
            package: Path to the package zip (e.g. produced by
                `blueye bundle-model`).
            timeout: Request timeout in seconds; model files can be large.

        Returns:
            The installed model as reported by the drone.
        """
        package = Path(package)
        with package.open("rb") as file_handle:
            response = requests.post(
                f"{self._base_url}/upload", files={"file": file_handle}, timeout=timeout
            )
        model = CvModel.from_json(self._check(response).json())
        self._request_rescan()
        return model

    def delete(self, name: str, timeout: float = 5) -> None:
        """Delete a model package from the drone.

        Args:
            name: The package's directory slug (see CvModel.directory).
            timeout: Request timeout in seconds.
        """
        self._check(requests.delete(f"{self._base_url}/{name}", timeout=timeout))
        self._request_rescan()

    def download(
        self, name: str, output_path: Path | str | None = None, timeout: float = 60
    ) -> Path:
        """Download a model package from the drone as a zip.

        Args:
            name: The package's directory slug.
            output_path: Destination file or directory. Defaults to the filename the
                drone suggests (or `<name>.zip`) in the current directory.
            timeout: Request timeout in seconds.

        Returns:
            The path the zip was written to.
        """
        response = self._check(requests.get(f"{self._base_url}/{name}/download", timeout=timeout))
        disposition = response.headers.get("Content-Disposition", "")
        matches = re.findall('filename="([^"]+)"', disposition)
        filename = matches[0] if matches else f"{name}.zip"

        if output_path is None:
            output_path = Path(filename)
        else:
            output_path = Path(output_path)
            if output_path.is_dir():
                output_path = output_path / filename
        output_path.write_bytes(response.content)
        return output_path

    def set_enabled(self, name: str, enabled: bool, timeout: float = 5) -> None:
        """Enable or disable a model's autolaunch on the drone.

        Args:
            name: The package's directory slug.
            enabled: True to autolaunch the model, False to disable it.
            timeout: Request timeout in seconds.
        """
        self._check(
            requests.patch(
                f"{self._base_url}/{name}/enabled", json={"enabled": enabled}, timeout=timeout
            )
        )
        self._request_rescan()

    def set_device(self, name: str, device: str, timeout: float = 5) -> None:
        """Set the execution provider a model runs on.

        Args:
            name: The package's directory slug.
            device: One of :data:`VALID_DEVICES` ("cuda", "tensorrt",
                "tensorrt-dla0", "tensorrt-dla1").
            timeout: Request timeout in seconds.
        """
        self._check(
            requests.patch(
                f"{self._base_url}/{name}/device", json={"device": device}, timeout=timeout
            )
        )
        self._request_rescan()

    def set_hz(self, name: str, hz: int, timeout: float = 5) -> None:
        """Set a model's maximum inference rate.

        Args:
            name: The package's directory slug.
            hz: One of :data:`VALID_HZ` (0, 5, 10, 15); 0 means unlimited.
            timeout: Request timeout in seconds.
        """
        self._check(requests.patch(f"{self._base_url}/{name}/hz", json={"hz": hz}, timeout=timeout))
        self._request_rescan()

    def warmup(self, name: str, timeout: float = 600) -> None:
        """Pre-build the model's inference engine on the drone.

        For TensorRT devices this compiles the engine, which can take several
        minutes — subsequent launches then start instantly. Only available on the
        drone itself (the API answers 503 elsewhere).

        Args:
            name: The package's directory slug.
            timeout: Request timeout in seconds; engine builds are slow.
        """
        self._check(requests.post(f"{self._base_url}/{name}/warmup", timeout=timeout))

    def rescan(self, timeout: float | None = None) -> None:
        """Ask the drone's vision pipeline to rescan the installed packages.

        The request is the `RescanCvModelsCtrl` control message, so the drone has to be
        connected; an observer connection is enough. The drone has no file watcher, so a
        package uploaded, deleted or reconfigured stays as it was until a rescan or a reboot.
        [`upload`][blueye.sdk.cv_models.CvModels.upload],
        [`delete`][blueye.sdk.cv_models.CvModels.delete] and the `set_*` methods send one
        themselves while connected, so this is for changes made some other way. A rescan
        restarts every running model, and models only run while a client in control pets the
        watchdog.

        Args:
            timeout: Ignored. The rescan used to be an HTTP request with a timeout; the
                argument stays so code written for 2.8.0 keeps working.

        Raises:
            ConnectionError: If the drone is not connected.
        """
        if timeout is not None:
            warnings.warn(
                "`CvModels.rescan` sends a control message and no longer takes a timeout, "
                "the argument is ignored and will be removed in the next major version",
                DeprecationWarning,
                stacklevel=2,
            )
        self._parent_drone._ctrl_client.rescan_cv_models()

    def _request_rescan(self) -> None:
        """Send a rescan after a change, or say why not when the drone is not connected."""
        if self._parent_drone.connected:
            self._parent_drone._ctrl_client.rescan_cv_models()
        else:
            logger.warning(
                "The drone is not connected, so it has not been asked to rescan its CV models. "
                "The change takes effect after connect() and rescan(), or a reboot."
            )
