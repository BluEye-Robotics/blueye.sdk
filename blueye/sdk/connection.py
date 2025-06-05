from __future__ import annotations

import importlib.metadata
import logging
import platform
import queue
import threading
import uuid
from typing import Any, Callable, Dict, List, NamedTuple, Tuple

import blueye.protocol
import proto
import zmq

logger = logging.getLogger(__name__)


class WatchdogPublisher(threading.Thread):
    """A thread that publishes watchdog messages to keep the connection alive.

    Args:
        parent_drone (blueye.sdk.Drone): The parent drone instance.
        context (zmq.Context, optional): The ZeroMQ context.
    """

    def __init__(self, parent_drone: "blueye.sdk.Drone", context: zmq.Context = None):
        super().__init__(daemon=True)
        self._parent_drone = parent_drone
        self._context = context or zmq.Context().instance()
        self._socket = self._context.socket(zmq.PUB)
        self._socket.connect(f"tcp://{self._parent_drone._ip}:5557")
        self._exit_flag = threading.Event()

    def run(self):
        """Run the watchdog publisher thread."""
        duration = 0
        WATCHDOG_DELAY = 1
        while not self._exit_flag.wait(WATCHDOG_DELAY):
            self.pet_watchdog(duration)
            duration += 1

    def pet_watchdog(self, duration):
        """Send a watchdog message.

        Args:
            duration (int): The duration of the connection.
        """
        msg = blueye.protocol.WatchdogCtrl(
            connection_duration={"value": duration}, client_id=self._parent_drone.client_id
        )
        self._socket.send_multipart(
            [
                bytes(msg._pb.DESCRIPTOR.full_name, "utf-8"),
                blueye.protocol.WatchdogCtrl.serialize(msg),
            ]
        )

    def stop(self):
        """Stop the watchdog thread started by run()."""
        self._exit_flag.set()


class Callback(NamedTuple):
    """Specifications for callback for telemetry messages.

    Attributes:
        message_filter (List[proto.messages.Message]): The list of message types to filter.
        function (Callable[[str, proto.message.Message], None]): The callback function.
        pass_raw_data (bool): Whether to pass raw data to the callback.
        uuid_hex (str): The UUID of the callback in hexadecimal format.
        kwargs (Dict[str, Any]): Additional keyword arguments for the callback.
    """

    message_filter: List[proto.messages.Message]
    function: Callable[[str, proto.message.Message], None]
    pass_raw_data: bool
    uuid_hex: str
    kwargs: Dict[str, Any]


class TelemetryClient(threading.Thread):
    """A thread that handles telemetry messages from the drone"""

    def __init__(self, parent_drone: "blueye.sdk.Drone", context: zmq.Context = None):
        """Initialize the TelemetryClient.

        Args:
            parent_drone (blueye.sdk.Drone): The parent drone instance.
            context (zmq.Context, optional): The ZeroMQ context.
        """
        super().__init__(daemon=True)
        self._parent_drone = parent_drone
        self._context = context or zmq.Context().instance()
        self._socket = self._context.socket(zmq.SUB)
        self._socket.connect(f"tcp://{self._parent_drone._ip}:5555")
        self._socket.setsockopt_string(zmq.SUBSCRIBE, "")
        self._exit_flag = threading.Event()
        self._state_lock = threading.Lock()
        self._callbacks: List[Callback] = []
        self._state: Dict[proto.message.Message, bytes] = {}
        """`_state` is dictionary of the latest received messages, where the key is the protobuf
        message class, eg. blueye.protocol.DepthTel and the value is the serialized protobuf
        message"""

    def _handle_message(self, msg: Tuple[bytes, bytes]):
        """Handle an incoming telemetry message.

        Args:
            msg (Tuple[bytes, bytes]): The message type and payload.
        """
        msg_type_name = msg[0].decode("utf-8").replace("blueye.protocol.", "")
        try:
            msg_type = blueye.protocol.__getattribute__(msg_type_name)
        except AttributeError:
            # If a new telemetry message is introduced before the SDK is updated this can
            # be a common occurrence, so choosing to log with info instead of warning
            logger.info(f"Ignoring unknown message type: {msg_type_name}")
            return
        msg_payload = msg[1]
        with self._state_lock:
            self._state[msg_type] = msg_payload
        for callback in self._callbacks:
            if msg_type in callback.message_filter or callback.message_filter == []:
                if callback.pass_raw_data:
                    callback.function(msg_type_name, msg_payload, **callback.kwargs)
                else:
                    msg_deserialized = msg_type.deserialize(msg_payload)
                    callback.function(msg_type_name, msg_deserialized, **callback.kwargs)

    def run(self):
        """Run the telemetry client thread."""
        poller = zmq.Poller()
        poller.register(self._socket, zmq.POLLIN)

        while not self._exit_flag.is_set():
            events_to_be_processed = poller.poll(10)
            if len(events_to_be_processed) > 0:
                msg = self._socket.recv_multipart()
                self._handle_message(msg)

    def add_callback(
        self,
        msg_filter: List[proto.message.Message],
        callback_function: Callable[[str, proto.message.Message], None],
        raw: bool,
        **kwargs: Dict[str, Any],
    ) -> str:
        """Add a callback for telemetry messages.

        Args:
            msg_filter (List[proto.message.Message]): The list of message types to run the callback
                                                      function for.
            callback_function (Callable[[str, proto.message.Message], None]): The callback function.
            raw (bool): Whether to pass raw data to the callback.
            **kwargs: Additional keyword arguments for the callback.

        Returns:
            str: The UUID of the callback in hexadecimal format.
        """
        uuid_hex = uuid.uuid1().hex
        self._callbacks.append(Callback(msg_filter, callback_function, raw, uuid_hex, kwargs))
        return uuid_hex

    def remove_callback(self, callback_id: str):
        """Remove a callback by its UUID.

        Args:
            callback_id (str): The UUID of the callback to remove.
        """
        try:
            self._callbacks.pop([cb.uuid_hex for cb in self._callbacks].index(callback_id))
        except ValueError:
            logger.warning(f"Callback with id {callback_id} not found, ignoring")

    def get(self, key: proto.message.Message) -> bytes:
        """Get the latest received message of a specific type.

        Args:
            key (proto.message.Message): The message type to retrieve.

        Returns:
            bytes: The serialized message payload.
        """
        with self._state_lock:
            return self._state[key]

    def stop(self):
        """Stop the telemetry client thread."""
        self._exit_flag.set()


class CtrlClient(threading.Thread):
    """A thread that handles control messages to the drone."""

    def __init__(
        self,
        parent_drone: "blueye.sdk.Drone",
        context: zmq.Context = None,
    ):
        """Initialize the CtrlClient.

        Args:
            parent_drone (blueye.sdk.Drone): The parent drone instance.
            context (zmq.Context, optional): The ZeroMQ context.
        """
        super().__init__(daemon=True)
        self._context = context or zmq.Context().instance()
        self._parent_drone = parent_drone
        self._drone_pub_socket = self._context.socket(zmq.PUB)
        self._drone_pub_socket.connect(f"tcp://{self._parent_drone._ip}:5557")
        self._messages_to_send = queue.Queue()
        self._exit_flag = threading.Event()

    def run(self):
        """Run the control client thread."""
        while not self._exit_flag.is_set():
            try:
                msg = self._messages_to_send.get(timeout=0.1)
                self._drone_pub_socket.send_multipart(
                    [
                        bytes(msg._pb.DESCRIPTOR.full_name, "utf-8"),
                        msg.__class__.serialize(msg),
                    ]
                )
            except queue.Empty:
                # No messages to send, so we can
                continue

    def stop(self):
        """Stop the control client thread."""
        self._exit_flag.set()

    def set_lights(self, value: float):
        """Set the intensity of the lights.

        Args:
            value (float): The intensity value.
        """
        msg = blueye.protocol.LightsCtrl(lights={"value": value})
        self._messages_to_send.put(msg)

    def set_guest_port_lights(self, value: float):
        """Set the intensity of the guest port lights.

        Args:
            value (float): The intensity value.
        """
        msg = blueye.protocol.GuestportLightsCtrl(lights={"value": value})
        self._messages_to_send.put(msg)

    def set_water_density(self, value: float):
        """Set the water density.

        Args:
            value (float): The water density value.
        """
        msg = blueye.protocol.WaterDensityCtrl(density={"value": value})
        self._messages_to_send.put(msg)

    def set_tilt_velocity(self, value: float):
        """Set the tilt velocity.

        Args:
            value (float): The tilt velocity value.
        """
        msg = blueye.protocol.TiltVelocityCtrl(velocity={"value": value})
        self._messages_to_send.put(msg)

    def set_tilt_stabilization(self, enabled: bool):
        """Enable or disable tilt stabilization.

        Args:
            enabled (bool): Whether to enable tilt stabilization.
        """
        msg = blueye.protocol.TiltStabilizationCtrl(state={"enabled": enabled})
        self._messages_to_send.put(msg)

    def set_motion_input(
        self, surge: float, sway: float, heave: float, yaw: float, slow: float, boost: float
    ):
        """Set the motion input values.

        Args:
            surge (float): The surge value.
            sway (float): The sway value.
            heave (float): The heave value.
            yaw (float): The yaw value.
            slow (float): The slow value.
            boost (float): The boost value.
        """
        msg = blueye.protocol.MotionInputCtrl(
            motion_input={
                "surge": surge,
                "sway": sway,
                "heave": heave,
                "yaw": yaw,
                "slow": slow,
                "boost": boost,
            }
        )
        self._messages_to_send.put(msg)

    def set_auto_depth_state(self, enabled: bool):
        """Enable or disable auto depth control.

        Args:
            enabled (bool): Whether to enable auto depth control.
        """
        msg = blueye.protocol.AutoDepthCtrl(state={"enabled": enabled})
        self._messages_to_send.put(msg)

    def set_auto_heading_state(self, enabled: bool):
        """Enable or disable auto heading control.

        Args:
            enabled (bool): Whether to enable auto heading control.
        """
        msg = blueye.protocol.AutoHeadingCtrl(state={"enabled": enabled})
        self._messages_to_send.put(msg)

    def set_auto_altitude_state(self, enabled: bool):
        """Enable or disable auto altitude control.

        Args:
            enabled (bool): Whether to enable auto altitude control.
        """
        msg = blueye.protocol.AutoAltitudeCtrl(state={"enabled": enabled})
        self._messages_to_send.put(msg)

    def set_station_keeping_state(self, enabled: bool):
        """Enable or disable station keeping.

        Args:
            enabled (bool): Whether to enable station keeping.
        """
        msg = blueye.protocol.StationKeepingCtrl(state={"enabled": enabled})
        self._messages_to_send.put(msg)

    def set_weather_vaning_state(self, enabled: bool):
        """Enable or disable weather vaning.

        Args:
            enabled (bool): Whether to enable weather vaning.
        """
        msg = blueye.protocol.WeatherVaningCtrl(state={"enabled": enabled})
        self._messages_to_send.put(msg)

    def set_recording_state(self, main_enabled: bool, guestport_enabled: bool):
        """Enable or disable recording.

        Args:
            main_enabled (bool): Whether to enable main recording.
            guestport_enabled (bool): Whether to enable guest port recording.
        """
        msg = blueye.protocol.RecordCtrl(
            record_on={"main": main_enabled, "guestport": guestport_enabled}
        )
        self._messages_to_send.put(msg)

    def take_still_picture(self):
        """Take a still picture."""
        msg = blueye.protocol.TakePictureCtrl()
        self._messages_to_send.put(msg)

    def set_gripper_velocities(self, grip: float, rotation: float):
        """Set the gripper velocities.

        Args:
            grip (float): The grip velocity.
            rotation (float): The rotation velocity.
        """
        msg = blueye.protocol.GripperCtrl(
            gripper_velocities={"grip_velocity": grip, "rotate_velocity": rotation}
        )
        self._messages_to_send.put(msg)

    def set_laser_intensity(self, intensity: float):
        """Set the laser intensity.

        Args:
            intensity (float): The laser intensity value.
        """
        msg = blueye.protocol.LaserCtrl(laser={"value": intensity})
        self._messages_to_send.put(msg)

    def run_mission(self):
        msg = blueye.protocol.RunMissionCtrl()
        self._messages_to_send.put(msg)

    def pause_mission(self):
        msg = blueye.protocol.PauseMissionCtrl()
        self._messages_to_send.put(msg)

    def clear_mission(self):
        msg = blueye.protocol.ClearMissionCtrl()
        self._messages_to_send.put(msg)

    def set_multibeam_servo_angle(self, angle: float) -> None:
        """Set the angle of the servo on the multibeam skid.

        Args:
            angle (float): The angle in degrees.
        """
        msg = blueye.protocol.MultibeamServoCtrl(servo={"angle": angle})
        self._messages_to_send.put(msg)


class ReqRepClient(threading.Thread):
    """A thread that handles request-reply messages to and from the drone."""

    def __init__(self, parent_drone: "blueye.sdk.Drone", context: zmq.Context = None):
        """Initialize the ReqRepClient.

        Args:
            parent_drone (blueye.sdk.Drone): The parent drone instance.
            context (zmq.Context, optional): The ZeroMQ context.
        """
        super().__init__(daemon=True)
        self._context = context or zmq.Context().instance()
        self._parent_drone = parent_drone
        self._socket = self._context.socket(zmq.REQ)
        self._socket.connect(f"tcp://{self._parent_drone._ip}:5556")
        self._requests_to_send = queue.Queue()
        self._exit_flag = threading.Event()

    @staticmethod
    def _get_client_info() -> blueye.protocol.ClientInfo:
        """Get client information.

        Returns:
            blueye.protocol.ClientInfo: The client information.
        """
        client_info = blueye.protocol.ClientInfo(
            type="SDK",
            version=f"{importlib.metadata.version('blueye.sdk')}",
            device_type="Computer",
            platform=f"{platform.system()}",
            platform_version=f"{platform.release()}",
            name=f"{platform.node()}",
        )
        return client_info

    @staticmethod
    def _parse_type_to_string(msg: proto.message.MessageMeta | str) -> str:
        """Parse the message type to a string.

        Args:
            msg (proto.message.MessageMeta | str): The message type.

        Returns:
            str: The parsed message type as a string.
        """
        message_type = (
            msg.meta.full_name.replace("blueye.protocol.", "")
            if type(msg) is proto.message.MessageMeta
            else msg.replace("blueye.protocol.", "")
        )
        return message_type

    def run(self):
        """Run the request-reply client thread."""
        while not self._exit_flag.is_set():
            try:
                msg, response_type, response_callback_queue = self._requests_to_send.get(
                    timeout=0.1
                )
                self._socket.send_multipart(
                    [
                        bytes(msg._pb.DESCRIPTOR.full_name, "utf-8"),
                        msg.__class__.serialize(msg),
                    ]
                )
            except queue.Empty:
                # No requests to send, so we can
                continue
            # TODO: Deal with timeout
            resp = self._socket.recv_multipart()
            resp_deserialized = response_type.deserialize(resp[1])
            response_callback_queue.put(resp_deserialized)

    def stop(self):
        """Stop the request-reply client thread."""
        self._exit_flag.set()

    def _send_request_get_response(
        self,
        request: proto.message.Message,
        expected_response: proto.message.Message,
        timeout: float,
    ):
        """Send a request and get the response.

        Args:
            request (proto.message.Message): The request message.
            expected_response (proto.message.Message): The expected response message type.
            timeout (float): The timeout for the response.

        Returns:
            proto.message.Message: The response message.

        Raises:
            blueye.protocol.exceptions.ResponseTimeout: If no response is received before the timeout.
        """
        response_queue = queue.Queue(maxsize=1)
        self._requests_to_send.put((request, expected_response, response_queue))
        try:
            return response_queue.get(timeout=timeout)
        except queue.Empty:
            raise blueye.protocol.exceptions.ResponseTimeout(
                "No response received from drone before timeout"
            )

    def ping(self, timeout: float) -> blueye.protocol.PingRep:
        """Send a ping request to the drone.

        Args:
            timeout (float): The timeout for the response.

        Returns:
            blueye.protocol.PingRep: The ping response.
        """
        request = blueye.protocol.PingReq()
        return self._send_request_get_response(request, blueye.protocol.PingRep, timeout)

    def get_camera_parameters(
        self, camera: blueye.protocol.Camera, timeout: float = 0.05
    ) -> blueye.protocol.CameraParameters:
        """Get the camera parameters.

        Args:
            camera (blueye.protocol.Camera): The camera instance.
            timeout (float, optional): The timeout for the response.

        Returns:
            The camera parameters.
        """
        request = blueye.protocol.GetCameraParametersReq(camera=camera)
        response = self._send_request_get_response(
            request, blueye.protocol.GetCameraParametersRep, timeout
        )
        return response.camera_parameters

    def set_camera_parameters(
        self,
        parameters: blueye.protocol.CameraParameters,
        timeout: float = 0.05,
    ) -> blueye.protocol.SetCameraParametersRep:
        """Set the camera parameters.

        Args:
            parameters (blueye.protocol.CameraParameters): The camera parameters.
            timeout (float, optional): The timeout for the response.

        Returns:
            The response message.
        """
        request = blueye.protocol.SetCameraParametersReq(camera_parameters=parameters)
        return self._send_request_get_response(
            request, blueye.protocol.SetCameraParametersRep, timeout
        )

    def get_overlay_parameters(self, timeout: float = 0.05) -> blueye.protocol.OverlayParameters:
        """Get the overlay parameters.

        Args:
            timeout (float, optional): The timeout for the response.

        Returns:
            blueye.protocol.OverlayParameters: The overlay parameters.
        """
        request = blueye.protocol.GetOverlayParametersReq()
        response = self._send_request_get_response(
            request, blueye.protocol.GetOverlayParametersRep, timeout
        )
        return response.overlay_parameters

    def set_overlay_parameters(
        self, parameters: blueye.protocol.OverlayParameters, timeout: float = 0.05
    ) -> blueye.protocol.SetOverlayParametersRep:
        """Set the overlay parameters.

        Args:
            parameters (blueye.protocol.OverlayParameters): The overlay parameters.
            timeout (float, optional): The timeout for the response.

        Returns:
            The response message.
        """
        request = blueye.protocol.SetOverlayParametersReq(overlay_parameters=parameters)
        return self._send_request_get_response(
            request, blueye.protocol.SetOverlayParametersRep, timeout
        )

    def sync_time(self, time: int, timeout: float = 0.05) -> blueye.protocol.SyncTimeRep:
        """Synchronize the time with the drone.

        Args:
            time (int): The Unix timestamp to synchronize.
            timeout (float, optional): The timeout for the response.

        Returns:
            The response message.
        """
        request = blueye.protocol.SyncTimeReq(
            time={"unix_timestamp": {"seconds": time, "nanos": 0}}
        )
        return self._send_request_get_response(request, blueye.protocol.SyncTimeRep, timeout)

    def connect_client(
        self,
        client_info: blueye.protocol.ClientInfo = None,
        is_observer: bool = False,
        timeout: float = 0.05,
    ) -> blueye.protocol.ConnectClientRep:
        """Connect a client to the drone.

        Args:
            client_info (blueye.protocol.ClientInfo, optional): The client information.
            is_observer (bool, optional): Whether the client is an observer.
            timeout (float, optional): The timeout for the response.

        Returns:
            The connect client response.
        """
        client = client_info or self._get_client_info()
        client.is_observer = is_observer
        request = blueye.protocol.ConnectClientReq(client_info=client)
        return self._send_request_get_response(request, blueye.protocol.ConnectClientRep, timeout)

    def disconnect_client(
        self, client_id: int, timeout: float = 0.05
    ) -> blueye.protocol.DisconnectClientRep:
        """Disconnect a client from the drone.

        Args:
            client_id (int): The client ID.
            timeout (float, optional): The timeout for the response.

        Returns:
            The disconnect client response.
        """
        request = blueye.protocol.DisconnectClientReq(client_id=client_id)
        return self._send_request_get_response(
            request, blueye.protocol.DisconnectClientRep, timeout
        )

    def set_telemetry_msg_publish_frequency(
        self, msg: proto.message.MessageMeta | str, frequency: float, timeout: float = 0.05
    ) -> blueye.protocol.SetPubFrequencyRep:
        """Set the telemetry message publish frequency.

        Args:
            msg (proto.message.MessageMeta | str): The message type.
            frequency (float): The publish frequency.
            timeout (float, optional): The timeout for the response.

        Returns:
            The set publish frequency response.
        """
        message_type = self._parse_type_to_string(msg)
        request = blueye.protocol.SetPubFrequencyReq(
            message_type=message_type,
            frequency=frequency,
        )
        return self._send_request_get_response(request, blueye.protocol.SetPubFrequencyRep, timeout)

    def get_telemetry_msg(
        self, msg: proto.message.MessageMeta | str, timeout: float = 0.05
    ) -> blueye.protocol.GetTelemetryRep:
        """Get a telemetry message.

        Args:
            msg (proto.message.MessageMeta | str): The message type.
            timeout (float, optional): The timeout for the response.

        Returns:
            The telemetry message.
        """
        message_type = self._parse_type_to_string(msg)
        request = blueye.protocol.GetTelemetryReq(message_type=message_type)
        return self._send_request_get_response(request, blueye.protocol.GetTelemetryRep, timeout)

    def get_active_mission(self, timeout: float = 0.05) -> blueye.protocol.GetMissionRep:
        """Get the active mission from the drone"""
        request = blueye.protocol.GetMissionReq()
        return self._send_request_get_response(request, blueye.protocol.GetMissionRep, timeout)

    def set_mission(
        self, mission: blueye.protocol.Mission, timeout: float = 0.05
    ) -> blueye.protocol.SetMissionRep:
        """Send a new mission to the drone

        Requires that the drone is ready to receive a new mission.
        """
        request = blueye.protocol.SetMissionReq(mission=mission)
        return self._send_request_get_response(request, blueye.protocol.SetMissionRep, timeout)
