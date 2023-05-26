from __future__ import annotations

import importlib.metadata
import platform
import queue
import re
import threading
import uuid
from typing import Dict

import blueye.protocol
import proto
import zmq


class WatchdogPublisher(threading.Thread):
    def __init__(self, parent_drone: "blueye.sdk.Drone", context: zmq.Context = None):
        super().__init__(daemon=True)
        self._parent_drone = parent_drone
        self._context = context or zmq.Context().instance()
        self._socket = self._context.socket(zmq.PUB)
        self._socket.connect(f"tcp://{self._parent_drone._ip}:5557")
        self._exit_flag = threading.Event()

    def run(self):
        duration = 0
        WATCHDOG_DELAY = 1
        while not self._exit_flag.wait(WATCHDOG_DELAY):
            self.pet_watchdog(duration)
            duration += 1

    def pet_watchdog(self, duration):
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
        """Stop the watchdog thread started by run()"""
        self._exit_flag.set()


class TelemetryClient(threading.Thread):
    def __init__(self, parent_drone: "blueye.sdk.Drone", context: zmq.Context = None):
        super().__init__(daemon=True)
        self._parent_drone = parent_drone
        self._context = context or zmq.Context().instance()
        self._socket = self._context.socket(zmq.SUB)
        self._socket.connect(f"tcp://{self._parent_drone._ip}:5555")
        self._socket.setsockopt_string(zmq.SUBSCRIBE, "")
        self._exit_flag = threading.Event()
        self._state_lock = threading.Lock()
        self._callbacks = []
        self._state: Dict[proto.message.Message, bytes] = {}
        """`_state` is dictionary of the latest received messages, where the key is the protobuf
        message class, eg. blueye.protocol.DepthTel and the value is the serialized protobuf
        message"""

    def run(self):
        poller = zmq.Poller()
        poller.register(self._socket, zmq.POLLIN)

        while not self._exit_flag.is_set():
            events_to_be_processed = poller.poll(10)
            if len(events_to_be_processed) > 0:
                msg = self._socket.recv_multipart()
                msg_type = msg[0].decode("utf-8").replace("blueye.protocol.", "")
                msg_payload = msg[1]
                with self._state_lock:
                    self._state[msg_type] = msg_payload
                for cb in [cb for cb in self._callbacks if re.fullmatch(cb[0], msg_type)]:
                    if cb[2]:
                        cb[1](msg_type, msg_payload)
                    else:
                        try:
                            msg_object = blueye.protocol.__getattribute__(msg_type).deserialize(
                                msg_payload
                            )
                        except AttributeError:
                            # print(f"Message type {msg_type} not found in blueye.protocol")
                            # The message requested is not part of blueye.protocol. Remove callback
                            # self.remove_callback(cb[2])
                            pass
                        else:
                            cb[1](msg_type, msg_object)

    def add_callback(self, msg_type, callback, raw=False):
        mgs_type_without_prefix = msg_type.replace("blueye.protocol.", "")
        # if not mgs_type_without_prefix in dir(blueye.protocol):
        #    print(f"{mgs_type_without_prefix} not in blueye.protocol")
        #    return None
        try:
            re.compile(msg_type)
        except re.error:
            return None
        uuid_hex = uuid.uuid1().hex
        self._callbacks.append(tuple([mgs_type_without_prefix, callback, raw, uuid_hex]))
        return uuid_hex

    def remove_callback(self, callback_id):
        try:
            self._callbacks.pop([cb[3] for cb in self._callbacks].index(callback_id))
        except ValueError:
            pass

    def get(self, key: proto.message.Message):
        with self._state_lock:
            return self._state[key]

    def stop(self):
        self._exit_flag.set()


class CtrlClient(threading.Thread):
    def __init__(
        self,
        parent_drone: "blueye.sdk.Drone",
        context: zmq.Context = None,
    ):
        super().__init__(daemon=True)
        self._context = context or zmq.Context().instance()
        self._parent_drone = parent_drone
        self._drone_pub_socket = self._context.socket(zmq.PUB)
        self._drone_pub_socket.connect(f"tcp://{self._parent_drone._ip}:5557")
        self._messages_to_send = queue.Queue()
        self._exit_flag = threading.Event()

    def run(self):
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
        self._exit_flag.set()

    def set_lights(self, value: float):
        msg = blueye.protocol.LightsCtrl(lights={"value": value})
        self._messages_to_send.put(msg)

    def set_water_density(self, value: float):
        msg = blueye.protocol.WaterDensityCtrl(density={"value": value})
        self._messages_to_send.put(msg)

    def set_tilt_velocity(self, value: float):
        msg = blueye.protocol.TiltVelocityCtrl(velocity={"value": value})
        self._messages_to_send.put(msg)

    def set_tilt_stabilization(self, enabled: bool):
        msg = blueye.protocol.TiltStabilizationCtrl(state={"enabled": enabled})
        self._messages_to_send.put(msg)

    def set_motion_input(
        self, surge: float, sway: float, heave: float, yaw: float, slow: float, boost: float
    ):
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
        msg = blueye.protocol.AutoDepthCtrl(state={"enabled": enabled})
        self._messages_to_send.put(msg)

    def set_auto_heading_state(self, enabled: bool):
        msg = blueye.protocol.AutoHeadingCtrl(state={"enabled": enabled})
        self._messages_to_send.put(msg)

    def set_recording_state(self, main_enabled: bool, guestport_enabled: bool):
        msg = blueye.protocol.RecordCtrl(
            record_on={"main": main_enabled, "guestport": guestport_enabled}
        )
        self._messages_to_send.put(msg)

    def take_still_picture(self):
        msg = blueye.protocol.TakePictureCtrl()
        self._messages_to_send.put(msg)


class ReqRepClient(threading.Thread):
    def __init__(self, parent_drone: "blueye.sdk.Drone", context: zmq.Context = None):
        super().__init__(daemon=True)
        self._context = context or zmq.Context().instance()
        self._parent_drone = parent_drone
        self._socket = self._context.socket(zmq.REQ)
        self._socket.connect(f"tcp://{self._parent_drone._ip}:5556")
        self._requests_to_send = queue.Queue()
        self._exit_flag = threading.Event()

    def _get_client_info(self) -> blueye.protocol.ClientInfo:
        client_info = blueye.protocol.ClientInfo(
            type="SDK",
            version=f"{importlib.metadata.version('blueye.sdk')}",
            device_type="Computer",
            platform=f"{platform.system()}",
            platform_version=f"{platform.release()}",
            name=f"{platform.node()}",
        )
        return client_info

    def run(self):
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
        self._exit_flag.set()

    def ping(self, timeout: float) -> blueye.protocol.PingRep:
        request = blueye.protocol.PingReq()
        response_queue = queue.Queue(maxsize=1)
        self._requests_to_send.put((request, blueye.protocol.PingRep, response_queue))
        try:
            return response_queue.get(timeout=timeout)
        except queue.Empty:
            raise blueye.protocol.exceptions.ResponseTimeout(
                "No response received from drone before timeout"
            )

    def get_camera_parameters(
        self, camera: blueye.protocol.Camera, timeout: float = 0.05
    ) -> blueye.protocol.CameraParameters:
        request = blueye.protocol.GetCameraParametersReq(camera=camera)
        response_queue = queue.Queue(maxsize=1)
        self._requests_to_send.put(
            (request, blueye.protocol.GetCameraParametersRep, response_queue)
        )
        try:
            return response_queue.get(timeout=timeout).camera_parameters
        except queue.Empty:
            raise blueye.protocol.exceptions.ResponseTimeout(
                "No response received from drone before timeout"
            )

    def set_camera_parameters(
        self,
        parameters: blueye.protocol.CameraParameters,
        timeout: float = 0.05,
    ):
        request = blueye.protocol.SetCameraParametersReq(camera_parameters=parameters)
        response_queue = queue.Queue(maxsize=1)
        self._requests_to_send.put(
            (request, blueye.protocol.SetCameraParametersRep, response_queue)
        )
        try:
            response_queue.get(timeout=timeout)
        except queue.Empty:
            raise blueye.protocol.exceptions.ResponseTimeout(
                "No response received from drone before timeout"
            )

    def get_overlay_parameters(self, timeout: float = 0.05) -> blueye.protocol.OverlayParameters:
        request = blueye.protocol.GetOverlayParametersReq()
        response_queue = queue.Queue(maxsize=1)
        self._requests_to_send.put(
            (request, blueye.protocol.GetOverlayParametersRep, response_queue)
        )
        try:
            return response_queue.get(timeout=timeout).overlay_parameters
        except queue.Empty:
            raise blueye.protocol.exceptions.ResponseTimeout(
                "No response received from drone before timeout"
            )

    def set_overlay_parameters(
        self, parameters: blueye.protocol.OverlayParameters, timeout: float = 0.05
    ):
        request = blueye.protocol.SetOverlayParametersReq(overlay_parameters=parameters)
        response_queue = queue.Queue(maxsize=1)
        self._requests_to_send.put(
            (request, blueye.protocol.SetOverlayParametersRep, response_queue)
        )
        try:
            response_queue.get(timeout=timeout)
        except queue.Empty:
            raise blueye.protocol.exceptions.ResponseTimeout(
                "No response received from drone before timeout"
            )

    def sync_time(self, time: int, timeout: float = 0.05):
        request = blueye.protocol.SyncTimeReq(
            time={"unix_timestamp": {"seconds": time, "nanos": 0}}
        )
        response_queue = queue.Queue(maxsize=1)
        self._requests_to_send.put((request, blueye.protocol.SyncTimeRep, response_queue))
        try:
            response_queue.get(timeout=timeout)
        except queue.Empty:
            raise blueye.protocol.exceptions.ResponseTimeout(
                "No response received from drone before timeout"
            )

    def connect_client(
        self, client_info: blueye.protocol.ClientInfo = None, timeout: float = 0.05
    ) -> blueye.protocol.ConnectClientRep:
        client = client_info or self._get_client_info()
        request = blueye.protocol.ConnectClientReq(client_info=client)
        response_queue = queue.Queue(maxsize=1)
        self._requests_to_send.put((request, blueye.protocol.ConnectClientRep, response_queue))
        try:
            return response_queue.get(timeout=timeout)
        except queue.Empty:
            raise blueye.protocol.exceptions.ResponseTimeout(
                "No response received from drone before timeout"
            )

    def disconnect_client(
        self, client_id: int, timeout: float = 0.05
    ) -> blueye.protocol.DisconnectClientRep:
        request = blueye.protocol.DisconnectClientReq(client_id=client_id)
        response_queue = queue.Queue(maxsize=1)
        self._requests_to_send.put((request, blueye.protocol.DisconnectClientRep, response_queue))
        try:
            return response_queue.get(timeout=timeout)
        except queue.Empty:
            raise blueye.protocol.exceptions.ResponseTimeout(
                "No response received from drone before timeout"
            )

    def set_telemetry_msg_publish_frequency(
        self, msg: proto.message.Message | str, frequency: float, timeout: float = 0.05
    ) -> blueye.protocol.SetPubFrequencyRep:
        message_type = (
            msg.meta.full_name.replace("blueye.protocol.", "")
            if type(msg) == proto.message.Message
            else msg.replace("blueye.protocol.", "")
        )
        request = blueye.protocol.SetPubFrequencyReq(
            message_type=message_type,
            frequency=frequency,
        )
        response_queue = queue.Queue(maxsize=1)
        self._requests_to_send.put((request, blueye.protocol.SetPubFrequencyRep, response_queue))
        try:
            return response_queue.get(timeout=timeout)
        except queue.Empty:
            raise blueye.protocol.exceptions.ResponseTimeout(
                "No response received from drone before timeout"
            )
