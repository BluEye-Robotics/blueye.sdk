import importlib.metadata
import platform
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


