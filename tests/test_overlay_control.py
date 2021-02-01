import pytest
from blueye.sdk import DepthUnitOverlay, Drone, FontSizeOverlay, LogoOverlay, TemperatureUnitOverlay


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

    def test_enable_date(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.date_enabled = True
        mocked_drone._tcp_client.set_overlay_date_enabled.assert_called_with(1)
        mocked_drone.camera.overlay.date_enabled = False
        mocked_drone._tcp_client.set_overlay_date_enabled.assert_called_with(0)

    def test_get_date_state(self, mocked_drone: Drone):
        params = list(self.default_overlay_parameters)
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.date_enabled is False

        params[5] = 1
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.date_enabled is True

    def test_select_logo(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.logo = LogoOverlay.DISABLED
        mocked_drone._tcp_client.set_overlay_logo_index.assert_called_with(0)

        mocked_drone.camera.overlay.logo = LogoOverlay.BLUEYE
        mocked_drone._tcp_client.set_overlay_logo_index.assert_called_with(1)

        mocked_drone.camera.overlay.logo = LogoOverlay.CUSTOM
        mocked_drone._tcp_client.set_overlay_logo_index.assert_called_with(2)

    def test_select_logo_warns_and_ignores_for_out_of_range_value(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.logo = 3
        assert mocked_drone._tcp_client.set_overlay_logo_index.called is False

    def test_get_logo_state(self, mocked_drone: Drone):
        params = list(self.default_overlay_parameters)
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.logo == LogoOverlay["DISABLED"]

        params[6] = 1
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.logo == LogoOverlay["BLUEYE"]

        params[6] = 2
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.logo == LogoOverlay["CUSTOM"]

    def test_select_depth_unit(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.depth_unit = DepthUnitOverlay.METERS
        mocked_drone._tcp_client.set_overlay_depth_unit.assert_called_with(0)

        mocked_drone.camera.overlay.depth_unit = DepthUnitOverlay.FEET
        mocked_drone._tcp_client.set_overlay_depth_unit.assert_called_with(1)

    def test_select_depth_unit_warns_and_ignores_for_out_of_range_value(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.depth_unit = 2
        assert mocked_drone._tcp_client.set_overlay_depth_unit.called is False

    def test_get_depth_unit(self, mocked_drone: Drone):
        params = list(self.default_overlay_parameters)
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.depth_unit == DepthUnitOverlay["METERS"]

        params[7] = 1
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.depth_unit == DepthUnitOverlay["FEET"]

    def test_select_temp_unit(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.temperature_unit = TemperatureUnitOverlay.CELSIUS
        mocked_drone._tcp_client.set_overlay_temperature_unit.assert_called_with(0)

        mocked_drone.camera.overlay.temperature_unit = TemperatureUnitOverlay.FAHRENHEIT
        mocked_drone._tcp_client.set_overlay_temperature_unit.assert_called_with(1)

    def test_select_temp_unit_warns_and_ignores_for_out_of_range_value(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.temperature_unit = 2
        assert mocked_drone._tcp_client.set_overlay_temperature_unit.called is False

    def test_get_temp_unit(self, mocked_drone: Drone):
        params = list(self.default_overlay_parameters)
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.temperature_unit == TemperatureUnitOverlay["CELSIUS"]

        params[8] = 1
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.temperature_unit == TemperatureUnitOverlay["FAHRENHEIT"]

    def test_set_timezone_offset(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.timezone_offset = 120
        mocked_drone._tcp_client.set_overlay_tz_offset.assert_called_with(120)
        mocked_drone.camera.overlay.timezone_offset = -60
        mocked_drone._tcp_client.set_overlay_tz_offset.assert_called_with(-60)

    def test_get_timezone_offset(self, mocked_drone: Drone):
        params = list(self.default_overlay_parameters)
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.timezone_offset == 60

        params[9] = -60
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.timezone_offset == -60

    def test_set_margin_width(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.margin_width = 10
        mocked_drone._tcp_client.set_overlay_margin_width.assert_called_with(10)
        mocked_drone.camera.overlay.margin_width = 20
        mocked_drone._tcp_client.set_overlay_margin_width.assert_called_with(20)

    def test_get_margin_width(self, mocked_drone: Drone):
        params = list(self.default_overlay_parameters)
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.margin_width == 30

        params[10] = 60
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.margin_width == 60

    def test_sub_zero_margin_width_is_warned_and_ignored(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.margin_width = -10
        mocked_drone._tcp_client.set_overlay_margin_width.called is False

    def test_set_margin_height(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.margin_height = 10
        mocked_drone._tcp_client.set_overlay_margin_height.assert_called_with(10)
        mocked_drone.camera.overlay.margin_height = 20
        mocked_drone._tcp_client.set_overlay_margin_height.assert_called_with(20)

    def test_get_margin_height(self, mocked_drone: Drone):
        params = list(self.default_overlay_parameters)
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.margin_height == 15

        params[11] = 60
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.margin_height == 60

    def test_sub_zero_margin_height_is_warned_and_ignored(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.margin_height = -10
        mocked_drone._tcp_client.set_overlay_margin_height.called is False

    def test_select_font_size(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.font_size = FontSizeOverlay.PX15
        mocked_drone._tcp_client.set_overlay_font_size.assert_called_with(15)

        mocked_drone.camera.overlay.font_size = FontSizeOverlay.PX20
        mocked_drone._tcp_client.set_overlay_font_size.assert_called_with(20)

        mocked_drone.camera.overlay.font_size = FontSizeOverlay.PX25
        mocked_drone._tcp_client.set_overlay_font_size.assert_called_with(25)

        mocked_drone.camera.overlay.font_size = FontSizeOverlay.PX30
        mocked_drone._tcp_client.set_overlay_font_size.assert_called_with(30)

        mocked_drone.camera.overlay.font_size = FontSizeOverlay.PX35
        mocked_drone._tcp_client.set_overlay_font_size.assert_called_with(35)

        mocked_drone.camera.overlay.font_size = FontSizeOverlay.PX40
        mocked_drone._tcp_client.set_overlay_font_size.assert_called_with(40)

    def test_select_font_size_warns_and_ignores_for_out_of_range_value(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.font_size = 100
        assert mocked_drone._tcp_client.set_overlay_font_size.called is False

    def test_get_font_size(self, mocked_drone: Drone):
        params = list(self.default_overlay_parameters)
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.font_size == FontSizeOverlay(25)

        params[12] = 40
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.font_size == FontSizeOverlay(40)

    def test_set_title(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.title = "a" * 63
        mocked_drone._tcp_client.set_overlay_title.assert_called_with(b"a" * 63 + b"\x00")

    def test_set_title_warns_and_ignores_non_ascii(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.title = "æøå"
        assert mocked_drone._tcp_client.set_overlay_title.called is False

    def test_set_title_warns_and_truncates_too_long_title(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.title = "a" * 64
        mocked_drone._tcp_client.set_overlay_title.assert_called_with(b"a" * 63 + b"\x00")

    def test_get_title(self, mocked_drone: Drone):
        params = list(self.default_overlay_parameters)
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.title == ""

        params[13] = b"abc" * 21 + b"\x00"
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.title == "abc" * 21

    def test_set_subtitle(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.subtitle = "a" * 63
        mocked_drone._tcp_client.set_overlay_subtitle.assert_called_with(b"a" * 63 + b"\x00")

    def test_set_subtitle_warns_and_ignores_non_ascii(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.subtitle = "æøå"
        assert mocked_drone._tcp_client.set_overlay_subtitle.called is False

    def test_set_subtitle_warns_and_truncates_too_long_subtitle(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.subtitle = "a" * 64
        mocked_drone._tcp_client.set_overlay_subtitle.assert_called_with(b"a" * 63 + b"\x00")

    def test_get_subtitle(self, mocked_drone: Drone):
        params = list(self.default_overlay_parameters)
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.subtitle == ""

        params[14] = b"abc" * 21 + b"\x00"
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.subtitle == "abc" * 21

    def test_set_date_format(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.date_format = "a" * 63
        mocked_drone._tcp_client.set_overlay_date_format.assert_called_with(b"a" * 63 + b"\x00")

    def test_set_date_format_warns_and_ignores_non_ascii(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.date_format = "æøå"
        assert mocked_drone._tcp_client.set_overlay_date_format.called is False

    def test_set_date_format_warns_and_truncates_too_long_date_format(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.date_format = "a" * 64
        mocked_drone._tcp_client.set_overlay_date_format.assert_called_with(b"a" * 63 + b"\x00")

    def test_get_date_format(self, mocked_drone: Drone):
        params = list(self.default_overlay_parameters)
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.date_format == "%m/%d/%Y %I:%M:%S %p"

        params[15] = b"abc" * 21 + b"\x00"
        mocked_drone._tcp_client.get_overlay_parameters.return_value = params
        assert mocked_drone.camera.overlay.date_format == "abc" * 21

    def test_upload_logo(self, mocked_drone: Drone, requests_mock, mocker):
        requests_mock.post("http://192.168.1.101/asset/logo")
        mocked_open = mocker.patch("builtins.open", mocker.mock_open())
        logo_path = "/tmp/logo.png"

        mocked_drone.camera.overlay.upload_logo(logo_path)

        mocked_open.assert_called_once_with(logo_path, "rb")

    def test_upload_raises_exception_for_400s(self, mocked_drone: Drone, requests_mock, mocker):
        from requests.exceptions import HTTPError

        requests_mock.post("http://192.168.1.101/asset/logo", status_code=400)
        mocker.patch("builtins.open", mocker.mock_open())
        with pytest.raises(HTTPError):
            mocked_drone.camera.overlay.upload_logo("whatever.png")

    def test_download_logo_default_path(self, mocked_drone: Drone, requests_mock, mocker):
        png_content = b"Don't look too close, I'm a png I swear"
        filename = "logo.png"
        headers = {"Content-Disposition": f'inline; filename="{filename}"'}
        requests_mock.get("http://192.168.1.101/asset/logo", content=png_content, headers=headers)
        mocked_open = mocker.patch("builtins.open", mocker.mock_open())
        mocked_drone.camera.overlay.download_logo()
        mocked_open.assert_called_once_with(f"./{filename}", "wb")
        mocked_filehandle = mocked_open()
        mocked_filehandle.write.assert_called_once_with(png_content)

    def test_download_logo_raises_exception_for_404(self, mocked_drone: Drone, requests_mock):
        from requests.exceptions import HTTPError

        requests_mock.get("http://192.168.1.101/asset/logo", status_code=404)
        with pytest.raises(HTTPError):
            mocked_drone.camera.overlay.download_logo()
