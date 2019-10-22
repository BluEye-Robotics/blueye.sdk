import json
from datetime import datetime

import pytest

from blueye.sdk.logs import LogFile, Logs


@pytest.fixture
def logListWithTwoLogs(requests_mock):
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
    return Logs("192.168.1.101")


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
def test_humanReadableFilesizes(binsize, expected_output):
    logfile = LogFile(0, "name", "2019-01-01T00:00:00.000000", binsize, "192.168.1.101")
    assert logfile._humanReadableFilesize() == expected_output


@pytest.mark.parametrize(
    "isoformatString, expectedDatetime",
    [("2019-01-01T00:00:00.000000", datetime(2019, 1, 1, 0, 0, 0, 0))],
)
def test_TimestampIsoformatConversion(isoformatString, expectedDatetime):
    logfile = LogFile(0, "", isoformatString, 0, "192.168.1.101")
    assert logfile.timestamp == expectedDatetime


def test_defaultDownloadPath(requests_mock, mocker):
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


def test_logfileFormattingWithHeader():
    log = LogFile(1000, "log1.csv", "2019-01-01T00:00:00.000000", 1024, "192.168.1.101")
    expected_output = (
        "Name                        Time                Max depth  Size\n"
        + "log1.csv                    01. Jan 2019 00:00  1.00 m     1.0 KiB"
    )
    assert f"{log:withHeader}" == expected_output


def test_logfileFormattingWithoutHeader():
    log = LogFile(1000, "log1.csv", "2019-01-01T00:00:00.000000", 1024, "192.168.1.101")
    expected_output = (
        "log1.csv                    01. Jan 2019 00:00  1.00 m     1.0 KiB"
    )
    assert f"{log}" == expected_output


def test_loglistFormatting(logListWithTwoLogs):
    expected_output = (
        "Name                        Time                Max depth  Size\n"
        + "log1.csv                    01. Jan 2019 00:00  1.00 m     1.0 KiB\n"
        + "log2.csv                    02. Jan 2019 00:00  2.00 m     2.0 KiB\n"
    )
    assert f"{logListWithTwoLogs}" == expected_output


def test_logListIsSubscriptable(logListWithTwoLogs):
    assert logListWithTwoLogs[0].name == "log1.csv"
    assert logListWithTwoLogs[1].name == "log2.csv"


def test_logListIsAccessibleByKey(logListWithTwoLogs):
    assert logListWithTwoLogs["log1.csv"]


def test_logListIsIterable(logListWithTwoLogs):
    expected_names = "log1.csvlog2.csv"
    names = ""
    for log in logListWithTwoLogs:
        names += log.name
    assert names == expected_names
