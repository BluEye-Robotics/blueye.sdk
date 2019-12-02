class Camera:
    def __init__(self, tcp_client, state_watcher):
        self._tcp_client = tcp_client
        self._state_watcher = state_watcher

    @property
    def is_recording(self) -> bool:
        state = self._state_watcher.general_state
        if state["camera_record_time"] != -1:
            return True
        else:
            return False

    @is_recording.setter
    def is_recording(self, start_recording: bool):
        if start_recording:
            self._tcp_client.start_recording()
        else:
            self._tcp_client.stop_recording()

    @property
    def bitrate(self) -> int:
        camera_parameters = self._tcp_client.get_camera_parameters()
        bitrate = camera_parameters[1]
        return bitrate

    @bitrate.setter
    def bitrate(self, bitrate: int):
        self._tcp_client.set_camera_bitrate(bitrate)

    @property
    def exposure(self) -> int:
        camera_parameters = self._tcp_client.get_camera_parameters()
        exposure = camera_parameters[2]
        return exposure

    @exposure.setter
    def exposure(self, exposure: int):
        self._tcp_client.set_camera_exposure(exposure)

    @property
    def whitebalance(self) -> int:
        camera_parameters = self._tcp_client.get_camera_parameters()
        whitebalance = camera_parameters[3]
        return whitebalance

    @whitebalance.setter
    def whitebalance(self, whitebalance: int):
        self._tcp_client.set_camera_whitebalance(whitebalance)

    @property
    def hue(self) -> int:
        camera_parameters = self._tcp_client.get_camera_parameters()
        hue = camera_parameters[4]
        return hue

    @hue.setter
    def hue(self, hue: int):
        self._tcp_client.set_camera_hue(hue)

    @property
    def resolution(self) -> int:
        camera_parameters = self._tcp_client.get_camera_parameters()
        resolution = camera_parameters[5]
        return resolution

    @resolution.setter
    def resolution(self, resolution: int):
        self._tcp_client.set_camera_resolution(resolution)

    @property
    def framerate(self) -> int:
        camera_parameters = self._tcp_client.get_camera_parameters()
        framerate = camera_parameters[6]
        return framerate

    @framerate.setter
    def framerate(self, framerate: int):
        self._tcp_client.set_camera_framerate(framerate)

    @property
    def record_time(self) -> int:
        return self._state_watcher.general_state["camera_record_time"]
