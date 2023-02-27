import importlib.metadata
import platform
import queue
import threading

import blueye.protocol
import proto
import zmq


class WatchdogPublisher(threading.Thread):
    def __init__(self, parent_drone: "blueye.sdk.Drone", context: zmq.Context = None):
        super().__init__()
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
        self.client_id = self._get_client_id()
        while not self._exit_flag.wait(WATCHDOG_DELAY):
            self.pet_watchdog(duration)
            duration += 1

    def pet_watchdog(self, duration):
        msg = blueye.protocol.WatchdogCtrl(
            connection_duration={"value": duration}, client_id=self.client_id
        )
        self.socket.send_multipart(
            [
                bytes(msg._pb.DESCRIPTOR.full_name, "utf-8"),
                blueye.protocol.WatchdogCtrl.serialize(msg),
            ]
        )

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

    def _get_full_msg_name(self, msg: proto.Message) -> str:
        return msg._pb.DESCRIPTOR.full_name

    def _get_client_id(self, context=None) -> int:
        context = context or zmq.Context.instance()
        socket = context.socket(zmq.REQ)
        socket.connect(f"tcp://{self.drone_ip}:5556")
        msg = blueye.protocol.ConnectClientReq(client_info=self._get_client_info())

        socket.send_multipart(
            [
                bytes(self._get_full_msg_name(msg), "utf-8"),
                blueye.protocol.ConnectClientReq.serialize(msg),
            ]
        )

        resp = socket.recv_multipart()
        resp_deserialized = blueye.protocol.ConnectClientRep.deserialize(resp[1])
        return resp_deserialized.client_id

    def stop(self):
        """Stop the watchdog thread started by run()"""
        self._exit_flag.set()


class TelemetryClient(threading.Thread):
    def __init__(self, parent_drone: "blueye.sdk.Drone", context: zmq.Context = None):
        super().__init__()
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
        super().__init__()
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
