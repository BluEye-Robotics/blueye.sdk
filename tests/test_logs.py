import json
from datetime import datetime

import pytest

from blueye.sdk.logs import LogFile, Logs


@pytest.fixture
def log_list_with_two_logs(requests_mock, mocker):
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
    mocked_pioneer = mocker.patch("blueye.sdk.Pioneer", autospec=True, _ip="192.168.1.101")
    return Logs(mocked_pioneer)


@pytest.mark.parametrize(
    "binsize, expected_output",
    [
        (0, "0.0 B"),
        (512, "512.0 B"),
        (1024, "1.0 KiB"),
        (1024 ** 2, "1.0 MiB"),
        (1024 ** 3, "1.0 GiB"),
    ],
)
def test_human_readable_filesizes(binsize, expected_output):
    logfile = LogFile(0, "name", "2019-01-01T00:00:00.000000", binsize, "192.168.1.101")
    assert logfile._human_readable_filesize() == expected_output


@pytest.mark.parametrize(
    "isoformat_string, expected_datetime",
    [("2019-01-01T00:00:00.000000", datetime(2019, 1, 1, 0, 0, 0, 0))],
)
def test_timestamp_isoformat_conversion(isoformat_string, expected_datetime):
    logfile = LogFile(0, "", isoformat_string, 0, "192.168.1.101")
    assert logfile.timestamp == expected_datetime


def test_default_download_path(requests_mock, mocker):
    logname = "log.csv"
    dummylog = LogFile(0, logname, "2019-01-01T00:00:00.000000", 0, "192.168.1.101")

    dummy_csv_content = b"1,2,3"
    requests_mock.get(
        f"http://192.168.1.101/logcsv/{logname}", content=dummy_csv_content
    )

    mocked_open = mocker.patch("builtins.open", mocker.mock_open())

    dummylog.download()

    mocked_open.assert_called_once_with(f"./{logname}", "wb")
    mocked_filehandle = mocked_open()
    mocked_filehandle.write.assert_called_once_with(dummy_csv_content)


def test_logfile_formatting_with_header():
    log = LogFile(1000, "log1.csv", "2019-01-01T00:00:00.000000", 1024, "192.168.1.101")
    expected_output = (
        "Name      Time                Max depth    Size\n"
        + "log1.csv  01. Jan 2019 00:00  1.00 m       1.0 KiB"
    )
    assert f"{log:with_header}" == expected_output


def test_logfile_formatting_without_header():
    log = LogFile(1000, "log1.csv", "2019-01-01T00:00:00.000000", 1024, "192.168.1.101")
    expected_output = "log1.csv  01. Jan 2019 00:00  1.00 m  1.0 KiB"
    assert f"{log}" == expected_output


def test_loglist_formatting(log_list_with_two_logs):
    expected_output = (
        "Name      Time                Max depth    Size\n"
        + "log1.csv  01. Jan 2019 00:00  1.00 m       1.0 KiB\n"
        + "log2.csv  02. Jan 2019 00:00  2.00 m       2.0 KiB"
    )
    assert f"{log_list_with_two_logs}" == expected_output


def test_log_list_is_subscriptable(log_list_with_two_logs):
    assert log_list_with_two_logs[0].name == "log1.csv"
    assert log_list_with_two_logs[1].name == "log2.csv"


def test_log_list_is_accessible_by_key(log_list_with_two_logs):
    assert log_list_with_two_logs["log1.csv"]


def test_log_list_is_iterable(log_list_with_two_logs):
    expected_names = "log1.csvlog2.csv"
    names = ""
    for log in log_list_with_two_logs:
        names += log.name
    assert names == expected_names


def test_logs_raises_KeyError(log_list_with_two_logs):
    with pytest.raises(KeyError):
        log_list_with_two_logs["non_existing_log_name"]


def test_logs_raises_IndexError(log_list_with_two_logs):
    with pytest.raises(IndexError):
        log_list_with_two_logs[3]
