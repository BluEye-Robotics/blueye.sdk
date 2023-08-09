import json
from datetime import datetime

import pytest

from blueye.sdk.logs import LegacyLogFile, LegacyLogs, Logs, human_readable_filesize


@pytest.fixture
def Logs_object_with_two_logs(requests_mock, mocker):
    dummy_json = json.dumps(
        [
            {
                "binlog_size": 1024,
                "has_binlog": True,
                "has_dive_info": True,
                "is_dive": True,
                "is_open": False,
                "log_number": 1,
                "name": "BYEDP123456_aabbccddeeff1234_00001",
                "videos": [
                    "/videos/video_BYEDP123456_2023-08-02_122432.mp4",
                    "/videos/video_BYEDP123456_2023-08-02_122444_cam2.mp4",
                ],
            },
            {
                "binlog_size": 2048,
                "has_binlog": True,
                "has_dive_info": True,
                "is_dive": True,
                "is_open": False,
                "log_number": 2,
                "name": "BYEDP123456_aabbccddeeff1234_00002",
                "videos": [
                    "/videos/video_BYEDP123456_2023-08-03_122432.mp4",
                    "/videos/video_BYEDP123456_2023-08-03_122444_cam2.mp4",
                ],
            },
        ]
    )
    requests_mock.get("http://192.168.1.101/logs", content=str.encode(dummy_json))

    log1_json = json.dumps(
        {
            "blunux_version": "3.2.63-honister-master",
            "is_dive": True,
            "is_valid": True,
            "log_name": "BYEDP123456_aabbccddeeff1234_00001.bez",
            "max_depth_magnitude": 100,
            "model_name": "Blueye X3",
            "start_time": 1690979463,
            "videos": [
                "/videos/video_BYEDP123456_2023-08-02_123249.mp4",
                "/videos/video_BYEDP123456_2023-08-02_123255_cam2.mp4",
            ],
        }
    )
    log2_json = json.dumps(
        {
            "blunux_version": "3.2.63-honister-master",
            "is_dive": True,
            "is_valid": True,
            "log_name": "BYEDP123456_aabbccddeeff1234_00001.bez",
            "max_depth_magnitude": 10,
            "model_name": "Blueye X3",
            "start_time": 1691065863,
            "videos": [
                "/videos/video_BYEDP123456_2023-08-03_123249.mp4",
                "/videos/video_BYEDP123456_2023-08-03_123255_cam2.mp4",
            ],
        }
    )
    requests_mock.get(
        "http://192.168.1.101/logs/BYEDP123456_aabbccddeeff1234_00001/dive_info",
        content=str.encode(log1_json),
    )
    requests_mock.get(
        "http://192.168.1.101/logs/BYEDP123456_aabbccddeeff1234_00002/dive_info",
        content=str.encode(log2_json),
    )
    mocked_drone = mocker.patch(
        "blueye.sdk.Drone", autospec=True, _ip="192.168.1.101", software_version_short="3.2.63"
    )
    mocked_drone.connected = True
    return Logs(mocked_drone)


def test_logs_len_return_two(Logs_object_with_two_logs):
    assert len(Logs_object_with_two_logs) == 2


def test_logs_filter(Logs_object_with_two_logs):
    assert len(Logs_object_with_two_logs.filter(lambda log: log.is_dive == True)) == 2
    assert len(Logs_object_with_two_logs.filter(lambda log: log.max_depth_magnitude > 50)) == 1


@pytest.fixture
def legacy_log_list_with_two_logs(requests_mock, mocker):
    dummy_json = json.dumps(
        [
            {
                "maxdepth": 1000,
                "name": "log1.csv",
                "timestamp": "2019-01-01T00:00:00.000000",
                "binsize": 1024,
            },
            {
                "maxdepth": 2000,
                "name": "log2.csv",
                "timestamp": "2019-01-02T00:00:00.000000",
                "binsize": 2048,
            },
        ]
    )

    requests_mock.get(f"http://192.168.1.101/logcsv", content=str.encode(dummy_json))
    mocked_drone = mocker.patch("blueye.sdk.Drone", autospec=True, _ip="192.168.1.101")
    mocked_drone.connected = True
    return LegacyLogs(mocked_drone)


@pytest.mark.parametrize(
    "binsize, expected_output",
    [
        (0, "0.0 B"),
        (512, "512.0 B"),
        (1024, "1.0 KiB"),
        (1024**2, "1.0 MiB"),
        (1024**3, "1.0 GiB"),
    ],
)
def test_human_readable_filesizes(binsize, expected_output):
    assert human_readable_filesize(binsize) == expected_output


@pytest.mark.parametrize(
    "isoformat_string, expected_datetime",
    [("2019-01-01T00:00:00.000000", datetime(2019, 1, 1, 0, 0, 0, 0))],
)
def test_legacy_timestamp_isoformat_conversion(isoformat_string, expected_datetime):
    logfile = LegacyLogFile(0, "", isoformat_string, 0, "192.168.1.101")
    assert logfile.timestamp == expected_datetime


def test_legacy_default_download_path(requests_mock, mocker):
    logname = "log.csv"
    dummylog = LegacyLogFile(0, logname, "2019-01-01T00:00:00.000000", 0, "192.168.1.101")

    dummy_csv_content = b"1,2,3"
    requests_mock.get(f"http://192.168.1.101/logcsv/{logname}", content=dummy_csv_content)

    mocked_open = mocker.patch("builtins.open", mocker.mock_open())

    dummylog.download()

    mocked_open.assert_called_once_with(f"./{logname}", "wb")
    mocked_filehandle = mocked_open()
    mocked_filehandle.write.assert_called_once_with(dummy_csv_content)


def test_legacy_logfile_formatting_with_header():
    log = LegacyLogFile(1000, "log1.csv", "2019-01-01T00:00:00.000000", 1024, "192.168.1.101")
    expected_output = (
        "Name      Time                Max depth    Size\n"
        + "log1.csv  01. Jan 2019 00:00  1.00 m       1.0 KiB"
    )
    assert f"{log:with_header}" == expected_output


def test_legacy_logfile_formatting_without_header():
    log = LegacyLogFile(1000, "log1.csv", "2019-01-01T00:00:00.000000", 1024, "192.168.1.101")
    expected_output = "log1.csv  01. Jan 2019 00:00  1.00 m  1.0 KiB"
    assert f"{log}" == expected_output


def test_legacy_loglist_formatting(legacy_log_list_with_two_logs):
    expected_output = (
        "Name      Time                Max depth    Size\n"
        + "log1.csv  01. Jan 2019 00:00  1.00 m       1.0 KiB\n"
        + "log2.csv  02. Jan 2019 00:00  2.00 m       2.0 KiB"
    )
    assert f"{legacy_log_list_with_two_logs}" == expected_output


def test_legacy_log_list_is_subscriptable(legacy_log_list_with_two_logs):
    assert legacy_log_list_with_two_logs[0].name == "log1.csv"
    assert legacy_log_list_with_two_logs[1].name == "log2.csv"


def test_legacy_log_list_is_accessible_by_key(legacy_log_list_with_two_logs):
    assert legacy_log_list_with_two_logs["log1.csv"]


def test_legacy_log_list_is_iterable(legacy_log_list_with_two_logs):
    expected_names = "log1.csvlog2.csv"
    names = ""
    for log in legacy_log_list_with_two_logs:
        names += log.name
    assert names == expected_names


def test_legacy_logs_raises_KeyError(legacy_log_list_with_two_logs):
    with pytest.raises(KeyError):
        legacy_log_list_with_two_logs["non_existing_log_name"]


def test_legacy_logs_raises_IndexError(legacy_log_list_with_two_logs):
    with pytest.raises(IndexError):
        legacy_log_list_with_two_logs[3]


def test_legacy_index_is_downloaded_on_first_access(legacy_log_list_with_two_logs):
    """Tests that logs are not downloaded before someone attempts to access the logs. And that the
    logs are downloaded after an access is attempted.
    """
    assert legacy_log_list_with_two_logs._logs == {}
    _ = legacy_log_list_with_two_logs[0]
    assert len(legacy_log_list_with_two_logs[::]) == 2


@pytest.mark.parametrize("divisor", [1, 10])
def test_legacy_divisor_parameter_is_passed_to_request(requests_mock, mocker, divisor):
    logname = "log.csv"
    dummylog = LegacyLogFile(0, logname, "2019-01-01T00:00:00.000000", 0, "192.168.1.101")

    dummy_csv_content = b"1,2,3"
    requests_mock.get(
        f"http://192.168.1.101/logcsv/{logname}?divisor={divisor}", content=dummy_csv_content
    )

    mocker.patch("builtins.open", mocker.mock_open())

    dummylog.download(downsample_divisor=divisor)
