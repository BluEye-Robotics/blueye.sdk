from blueye.sdk import Drone


class TestOverlay:
    default_overlay_parameters = (
        97,  # Parameter
        0,  # Temperature enabled
        0,  # Depth enabled
        0,  # Heading enabled
        0,  # Tilt enabled
        0,  # Date enabled
        0,  # Logo index
        0,  # Depth unit (index)
        0,  # Temperature unit (index)
        60,  # Timezone offset
        30,  # Margin width
        15,  # Margin height
        25,  # Font size
        # Title
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
        # Subtitle
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
        # Data format
        b"%m/%d/%Y %I:%M:%S %p\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
    )

    def test_enable_temperature(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.temperature_enabled = True
        mocked_drone._tcp_client.set_overlay_temperature_enabled.assert_called_with(1)
        mocked_drone.camera.overlay.temperature_enabled = False
        mocked_drone._tcp_client.set_overlay_temperature_enabled.assert_called_with(0)

    def test_get_temperature_state(self, mocked_drone: Drone):
        params = list(self.default_overlay_parameters)
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.temperature_enabled is False

        params[1] = 1
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.temperature_enabled is True

    def test_enable_depth(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.depth_enabled = True
        mocked_drone._tcp_client.set_overlay_depth_enabled.assert_called_with(1)
        mocked_drone.camera.overlay.depth_enabled = False
        mocked_drone._tcp_client.set_overlay_depth_enabled.assert_called_with(0)

    def test_get_depth_state(self, mocked_drone: Drone):
        params = list(self.default_overlay_parameters)
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.depth_enabled is False

        params[2] = 1
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.depth_enabled is True

    def test_enable_heading(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.heading_enabled = True
        mocked_drone._tcp_client.set_overlay_heading_enabled.assert_called_with(1)
        mocked_drone.camera.overlay.heading_enabled = False
        mocked_drone._tcp_client.set_overlay_heading_enabled.assert_called_with(0)

    def test_get_heading_state(self, mocked_drone: Drone):
        params = list(self.default_overlay_parameters)
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.heading_enabled is False

        params[3] = 1
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.heading_enabled is True

    def test_enable_tilt(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.tilt_enabled = True
        mocked_drone._tcp_client.set_overlay_tilt_enabled.assert_called_with(1)
        mocked_drone.camera.overlay.tilt_enabled = False
        mocked_drone._tcp_client.set_overlay_tilt_enabled.assert_called_with(0)

    def test_get_tilt_state(self, mocked_drone: Drone):
        params = list(self.default_overlay_parameters)
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.tilt_enabled is False

        params[4] = 1
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.tilt_enabled is True
