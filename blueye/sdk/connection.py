import importlib.metadata
import platform
import queue
import threading

import blueye.protocol
import proto
import zmq


class WatchdogPublisher(threading.Thread):
    def __init__(self, parent_drone: "blueye.sdk.Drone", context: zmq.Context = None):
        super().__init__(daemon=True)
        self._parent_drone = parent_drone
        self.drone_ip = self._parent_drone._ip
        self.port = 5557
        self.context = context or zmq.Context().instance()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.connect(f"tcp://{self.drone_ip}:{self.port}")
        self._exit_flag = threading.Event()

    def run(self):
        duration = 0
        WATCHDOG_DELAY = 1
        while not self._exit_flag.wait(WATCHDOG_DELAY):
            if self._parent_drone.in_control:
                self.pet_watchdog(duration)
                duration += 1

    def pet_watchdog(self, duration):
        msg = blueye.protocol.WatchdogCtrl(
            connection_duration={"value": duration}, client_id=self._parent_drone.client_id
        )
        self.socket.send_multipart(
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
        self.context = context or zmq.Context().instance()
        self.host = self._parent_drone._ip
        self.port = 5555
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(f"tcp://{self.host}:{self.port}")
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "")
        self._exit_flag = threading.Event()
        self.state = {}

    def run(self):
        poller = zmq.Poller()
        poller.register(self.socket, zmq.POLLIN)

        while not self._exit_flag.is_set():
            events_to_be_processed = poller.poll(10)
            if len(events_to_be_processed) > 0:
                msg = self.socket.recv_multipart()
                self.state[msg[0].decode("utf-8")] = msg[1]

    def stop(self):
        self._exit_flag.set()


class CtrlClient(threading.Thread):
    def __init__(
        self,
        parent_drone: "blueye.sdk.Drone",
        context: zmq.Context = None,
    ):
        super().__init__(daemon=True)
        self.context = context or zmq.Context().instance()
        self._parent_drone = parent_drone

        self.port = 5557
        self.drone_pub_socket = self.context.socket(zmq.PUB)
        self.drone_pub_socket.connect(f"tcp://{self._parent_drone._ip}:{self.port}")

        self.messages_to_send = queue.Queue()
        self._exit_flag = threading.Event()

    def run(self):
        while not self._exit_flag.is_set():
            try:
                msg = self.messages_to_send.get(timeout=0.5)
                self.drone_pub_socket.send_multipart(
                    [
                        bytes(msg._pb.DESCRIPTOR.full_name, "utf-8"),
                        msg.__class__.serialize(msg),
                    ]
                )
            except queue.Empty:
                pass

    def stop(self):
        self._exit_flag.set()

    def set_lights(self, value: float):
        msg = blueye.protocol.LightsCtrl(lights={"value": value})
        self.messages_to_send.put(msg)

    def set_water_density(self, value: float):
        msg = blueye.protocol.WaterDensityCtrl(density={"value": value})
        self.messages_to_send.put(msg)

    def set_tilt_velocity(self, value: float):
        msg = blueye.protocol.TiltVelocityCtrl(velocity={"value": value})
        self.messages_to_send.put(msg)

    def set_tilt_stabilization(self, enabled: bool):
        msg = blueye.protocol.TiltStabilizationCtrl(state={"enabled": enabled})
        self.messages_to_send.put(msg)

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
        self.messages_to_send.put(msg)

    def set_auto_depth_state(self, enabled: bool):
        msg = blueye.protocol.AutoDepthCtrl(state={"enabled": enabled})
        self.messages_to_send.put(msg)

    def set_auto_heading_state(self, enabled: bool):
        msg = blueye.protocol.AutoHeadingCtrl(state={"enabled": enabled})
        self.messages_to_send.put(msg)

    def set_recording_state(self, main_enabled: bool, guestport_enabled: bool):
        msg = blueye.protocol.RecordCtrl(
            record_on={"main": main_enabled, "guestport": guestport_enabled}
        )
        self.messages_to_send.put(msg)

    def take_still_picture(self):
        msg = blueye.protocol.TakePictureCtrl()
        self.messages_to_send.put(msg)


class ReqRepClient(threading.Thread):
    def __init__(self, parent_drone: "blueye.sdk.Drone", context: zmq.Context = None):
        super().__init__(daemon=True)
        self.context = context or zmq.Context().instance()
        self._parent_drone = parent_drone
        self.port = 5556
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(f"tcp://{self._parent_drone._ip}:{self.port}")
        self.requests_to_send = queue.Queue()
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
                msg, response_type, response_callback_queue = self.requests_to_send.get(timeout=0.1)
                self.socket.send_multipart(
                    [
                        bytes(msg._pb.DESCRIPTOR.full_name, "utf-8"),
                        msg.__class__.serialize(msg),
                    ]
                )
            except queue.Empty:
                continue
            # TODO: Deal with timeout
            resp = self.socket.recv_multipart()
            resp_deserialized = response_type.deserialize(resp[1])
            response_callback_queue.put(resp_deserialized)

    def stop(self):
        self._exit_flag.set()

    def ping(self, timeout: float) -> blueye.protocol.PingRep:
        request = blueye.protocol.PingReq()
        response_queue = queue.Queue(maxsize=1)
        self.requests_to_send.put((request, blueye.protocol.PingRep, response_queue))
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
        self.requests_to_send.put((request, blueye.protocol.GetCameraParametersRep, response_queue))
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
        self.requests_to_send.put((request, blueye.protocol.SetCameraParametersRep, response_queue))
        try:
            response_queue.get(timeout=timeout)
        except queue.Empty:
            raise blueye.protocol.exceptions.ResponseTimeout(
                "No response received from drone before timeout"
            )

    def get_overlay_parameters(self, timeout: float = 0.05) -> blueye.protocol.OverlayParameters:
        request = blueye.protocol.GetOverlayParametersReq()
        response_queue = queue.Queue(maxsize=1)
        self.requests_to_send.put(
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
        self.requests_to_send.put(
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
        self.requests_to_send.put((request, blueye.protocol.SyncTimeRep, response_queue))
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
        self.requests_to_send.put((request, blueye.protocol.ConnectClientRep, response_queue))
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
        self.requests_to_send.put((request, blueye.protocol.DisconnectClientRep, response_queue))
        try:
            return response_queue.get(timeout=timeout)
        except queue.Empty:
            raise blueye.protocol.exceptions.ResponseTimeout(
                "No response received from drone before timeout"
            )
