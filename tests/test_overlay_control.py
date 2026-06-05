import blueye.protocol as bp
import pytest

from blueye.sdk import Drone


class TestOverlay:
    def test_enable_temperature(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.enable_temperature(True)
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_once()

    def test_get_temperature_state(self, mocked_drone: Drone):
        assert mocked_drone.camera.overlay.is_temperature_enabled() is False

    def test_enable_depth(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.enable_depth(True)
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_once()

    def test_get_depth_state(self, mocked_drone: Drone):
        assert mocked_drone.camera.overlay.is_depth_enabled() is False

    def test_enable_heading(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.enable_heading(True)
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_once()

    def test_get_heading_state(self, mocked_drone: Drone):
        assert mocked_drone.camera.overlay.is_heading_enabled() is False

    def test_enable_tilt(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.enable_tilt(True)
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_once()

    def test_get_tilt_state(self, mocked_drone: Drone):
        assert mocked_drone.camera.overlay.is_tilt_enabled() is False

    def test_enable_date(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.enable_date(True)
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_once()

    def test_get_date_state(self, mocked_drone: Drone):
        assert mocked_drone.camera.overlay.is_date_enabled() is False

    def test_select_depth_unit(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.set_depth_unit(bp.DepthUnit.DEPTH_UNIT_METERS)
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_once()

    def test_select_depth_unit_warns_and_ignores_for_wrong_type(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.set_depth_unit("wrong type")
        assert mocked_drone._req_rep_client.set_overlay_parameters.called is False

    def test_get_depth_unit(self, mocked_drone: Drone):
        assert mocked_drone.camera.overlay.get_depth_unit() == bp.DepthUnit.DEPTH_UNIT_METERS

    def test_select_temp_unit(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.set_temperature_unit(
            bp.TemperatureUnit.TEMPERATURE_UNIT_CELSIUS
        )
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_once()

    def test_select_temp_unit_warns_and_ignores_for_wrong_type(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.set_temperature_unit("wrong type")
        assert mocked_drone._req_rep_client.set_overlay_parameters.called is False

    def test_get_temp_unit(self, mocked_drone: Drone):
        assert (
            mocked_drone.camera.overlay.get_temperature_unit()
            == bp.TemperatureUnit.TEMPERATURE_UNIT_CELSIUS
        )

    def test_enable_cp_probe(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.enable_cp_probe(True)
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_once()

    def test_get_cp_probe_state(self, mocked_drone: Drone):
        assert mocked_drone.camera.overlay.is_cp_probe_enabled() is False

    def test_distance_enabled(self, mocked_drone):
        mocked_drone.camera.overlay.enable_distance(True)
        assert mocked_drone.camera.overlay.is_distance_enabled()
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_once()

    def test_get_distance_enabled(self, mocked_drone):
        assert mocked_drone.camera.overlay.is_distance_enabled() is False

    def test_get_altitude_state(self, mocked_drone: Drone):
        assert mocked_drone.camera.overlay.is_altitude_enabled() is False

    def test_enable_altitude(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.enable_altitude(True)
        assert mocked_drone.camera.overlay.is_altitude_enabled()
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_once()

    def test_enable_thickness(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.enable_thickness(True)
        assert mocked_drone.camera.overlay.is_thickness_enabled()
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_once()

    def test_get_thickness_state(self, mocked_drone: Drone):
        assert mocked_drone.camera.overlay.is_thickness_enabled() is False

    def test_select_thickness_unit(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.set_thickness_unit(bp.ThicknessUnit.THICKNESS_UNIT_MILLIMETERS)
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_once()

    def test_select_thickness_unit_warns_and_ignores_for_wrong_type(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.set_thickness_unit("wrong type")
        assert mocked_drone._req_rep_client.set_overlay_parameters.called is False

    def test_get_thickness_unit(self, mocked_drone: Drone):
        assert (
            mocked_drone.camera.overlay.get_thickness_unit()
            == bp.ThicknessUnit.THICKNESS_UNIT_MILLIMETERS
        )

    def test_get_drone_location_state(self, mocked_drone: Drone):
        assert mocked_drone.camera.overlay.is_drone_location_enabled() is False

    def test_enable_drone_location(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.enable_drone_location(True)
        assert mocked_drone.camera.overlay.is_drone_location_enabled() is True
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_once()

    def test_get_shading(self, mocked_drone: Drone):
        assert mocked_drone.camera.overlay.get_shading() == 0

    def test_set_valid_shading(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.set_shading(0)
        assert mocked_drone.camera.overlay.get_shading() == 0
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_once()

    def test_set_invalid_shading_warns_and_ignores(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.set_shading(1.5)
            mocked_drone.camera.overlay.set_shading(-0.5)
        assert mocked_drone._req_rep_client.set_overlay_parameters.called is False

    def test_get_gamma_ray_measurement_state(self, mocked_drone: Drone):
        assert mocked_drone.camera.overlay.is_gamma_ray_measurement_enabled() is False

    def test_enable_gamma_ray_measurement(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.enable_gamma_ray_measurement(True)
        assert mocked_drone.camera.overlay.is_gamma_ray_measurement_enabled()
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_once()

    def test_set_timezone_offset(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.set_timezone_offset(120)
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_once()

    def test_get_timezone_offset(self, mocked_drone: Drone):
        assert mocked_drone.camera.overlay.get_timezone_offset() == 60

    def test_set_margin_width(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.set_margin_width(10)
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_once()

    def test_get_margin_width(self, mocked_drone: Drone):
        assert mocked_drone.camera.overlay.get_margin_width() == 30

    def test_sub_zero_margin_width_is_warned_and_ignored(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.set_margin_width(-10)
        mocked_drone._req_rep_client.set_overlay_parameters.called is False

    def test_set_margin_height(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.set_margin_height(10)
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_once()

    def test_get_margin_height(self, mocked_drone: Drone):
        assert mocked_drone.camera.overlay.get_margin_height() == 15

    def test_sub_zero_margin_height_is_warned_and_ignored(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.set_margin_height(-10)
        mocked_drone._req_rep_client.set_overlay_parameters.called is False

    def test_select_font_size(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.set_font_size(bp.FontSize.FONT_SIZE_PX15)
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_once()

    def test_select_font_size_warns_and_ignores_for_wrong_type(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.set_font_size("wrong type")
        assert mocked_drone._req_rep_client.set_overlay_parameters.called is False

    def test_get_font_size(self, mocked_drone: Drone):
        assert mocked_drone.camera.overlay.get_font_size() == bp.FontSize.FONT_SIZE_PX25

    def test_set_title(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.set_title("a" * 63)
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_once()

    def test_set_title_warns_and_ignores_non_ascii(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.set_title("æøå")
        assert mocked_drone._req_rep_client.set_overlay_parameters.called is False

    def test_set_title_warns_and_truncates_too_long_title(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.set_title("a" * 64)
        expected_params = mocked_drone._req_rep_client.get_overlay_parameters.return_value
        expected_params.title = "a" * 63
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_with(expected_params)

    def test_get_title(self, mocked_drone: Drone):
        assert mocked_drone.camera.overlay.get_title() == ""

    def test_set_subtitle(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.set_subtitle("a" * 63)
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_once()

    def test_set_subtitle_warns_and_ignores_non_ascii(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.set_subtitle("æøå")
        assert mocked_drone._req_rep_client.set_overlay_parameters.called is False

    def test_set_subtitle_warns_and_truncates_too_long_subtitle(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.set_subtitle("a" * 64)
        expected_params = mocked_drone._req_rep_client.get_overlay_parameters.return_value
        expected_params.subtitle = "a" * 63
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_with(expected_params)

    def test_get_subtitle(self, mocked_drone: Drone):
        assert mocked_drone.camera.overlay.get_subtitle() == ""

    def test_set_date_format(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.set_date_format("a" * 63)
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_once()

    def test_set_date_format_warns_and_ignores_non_ascii(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.set_date_format("æøå")
        assert mocked_drone._req_rep_client.set_overlay_parameters.called is False

    def test_set_date_format_warns_and_truncates_too_long_date_format(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.set_date_format("a" * 64)
        expected_params = mocked_drone._req_rep_client.get_overlay_parameters.return_value
        expected_params.date_format = "a" * 63
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_with(expected_params)

    def test_get_date_format(self, mocked_drone: Drone):
        assert mocked_drone.camera.overlay.get_date_format() == "%m/%d/%Y %I:%M:%S %p"


class TestOverlayLogoControl:
    def test_select_logo(self, mocked_drone: Drone):
        mocked_drone.camera.overlay.set_logo(bp.LogoType.LOGO_TYPE_NONE)
        mocked_drone._req_rep_client.set_overlay_parameters.assert_called_once()

    def test_select_logo_warns_and_ignores_on_invalid_type(self, mocked_drone: Drone):
        with pytest.warns(RuntimeWarning):
            mocked_drone.camera.overlay.set_logo("wrong type")
        assert mocked_drone._req_rep_client.set_overlay_parameters.called is False

    def test_get_logo_state(self, mocked_drone: Drone):
        assert mocked_drone.camera.overlay.get_logo() == bp.LogoType.LOGO_TYPE_NONE

    def test_upload_logo(self, mocked_drone: Drone, requests_mock, mocker):
        mocked_drone.software_version_short = "1.8.72"
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

    def test_delete_logo(self, mocked_drone: Drone, requests_mock):
        requests_mock.delete("http://192.168.1.101/asset/logo", text="Custom logo deleted!")
        mocked_drone.camera.overlay.delete_logo()

    def test_delete_logo_raises_exception_on_non_200(self, mocked_drone: Drone, requests_mock):
        requests_mock.delete("http://192.168.1.101/asset/logo", status_code=500)
        from requests.exceptions import HTTPError

        with pytest.raises(HTTPError):
            mocked_drone.camera.overlay.delete_logo()
