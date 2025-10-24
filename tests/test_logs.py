import gzip
import io
import json
from datetime import datetime

import blueye.protocol as bp
import pytest
from google.protobuf.any_pb2 import Any
from google.protobuf.internal.encoder import _VarintBytes
from google.protobuf.timestamp_pb2 import Timestamp

from blueye.sdk.logs import (
    LegacyLogFile,
    LegacyLogs,
    LogFile,
    Logs,
    LogStream,
    StreamingDecompressor,
    human_readable_filesize,
    is_gzip_compressed,
)


def create_real_binlog_record(unix_timestamp: int, clock_monotonic: int, payload_msg) -> bytes:
    """Create a real BinlogRecord with actual protobuf serialization"""
    # Serialize the payload message first
    payload_serialized = payload_msg.__class__.serialize(payload_msg)

    # Create an Any message manually with the correct type_url
    payload_type_name = payload_msg.__class__.__name__
    any_msg = Any(
        type_url=f"type.googleapis.com/blueye.protocol.{payload_type_name}",
        value=payload_serialized,
    )

    # Create Timestamp objects from the integer timestamps
    unix_ts = Timestamp()
    unix_ts.FromSeconds(unix_timestamp)

    mono_ts = Timestamp()
    mono_ts.FromSeconds(clock_monotonic)

    # Create the BinlogRecord
    binlog_record = bp.BinlogRecord(
        unix_timestamp=unix_ts, clock_monotonic=mono_ts, payload=any_msg
    )

    # Serialize the record
    serialized_record = bp.BinlogRecord.serialize(binlog_record)

    # Create varint for the message size using Google's protobuf encoder
    message_size = len(serialized_record)
    varint_bytes = _VarintBytes(message_size)

    return varint_bytes + serialized_record


def create_test_depth_message(depth_value: float) -> bp.DepthTel:
    """Create a test DepthTel message"""
    return bp.DepthTel(depth={"value": depth_value})


def create_test_battery_message(level: float) -> bp.BatteryTel:
    """Create a test BatteryTel message"""
    return bp.BatteryTel(battery={"level": level})


def create_test_attitude_message(roll: float, pitch: float, yaw: float) -> bp.AttitudeTel:
    """Create a test AttitudeTel message"""
    return bp.AttitudeTel(attitude={"roll": roll, "pitch": pitch, "yaw": yaw})


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


class TestGzipDetection:
    """Test the is_gzip_compressed function"""

    def test_gzip_magic_bytes_detected(self):
        """Test that gzip magic bytes are correctly detected"""
        gzip_data = b"\x1f\x8b" + b"some data"
        assert is_gzip_compressed(gzip_data) is True

    def test_non_gzip_data_not_detected(self):
        """Test that non-gzip data is correctly identified"""
        non_gzip_data = b"\x00\x01" + b"some data"
        assert is_gzip_compressed(non_gzip_data) is False

    def test_empty_data_not_detected(self):
        """Test that empty data is handled gracefully"""
        assert is_gzip_compressed(b"") is False

    def test_single_byte_not_detected(self):
        """Test that single byte data is handled gracefully"""
        assert is_gzip_compressed(b"\x1f") is False


class TestStreamingDecompressor:
    """Test the StreamingDecompressor class"""

    def test_uncompressed_data_passthrough(self):
        """Test that uncompressed data is passed through unchanged"""
        test_data = b"Hello, world! This is test data."
        decompressor = StreamingDecompressor(test_data)

        # Read all data
        result = decompressor.read(len(test_data))
        assert result == test_data

    def test_gzip_compressed_data_decompression(self):
        """Test that gzip compressed data is correctly decompressed"""
        original_data = b"Hello, world! This is test data for compression."
        compressed_data = gzip.compress(original_data)

        decompressor = StreamingDecompressor(compressed_data)

        # Read all data
        result = decompressor.read(len(original_data))
        assert result == original_data

    def test_partial_reads(self):
        """Test that partial reads work correctly"""
        test_data = b"Hello, world! This is a longer test message."
        decompressor = StreamingDecompressor(test_data)

        # Read data in chunks
        chunk1 = decompressor.read(5)
        chunk2 = decompressor.read(7)
        chunk3 = decompressor.read(100)  # Read more than remaining

        assert chunk1 == b"Hello"
        assert chunk2 == b", world"
        assert chunk3 == b"! This is a longer test message."

    def test_read_beyond_end(self):
        """Test that reading beyond end returns empty bytes"""
        test_data = b"Short"
        decompressor = StreamingDecompressor(test_data)

        # Read all data
        result1 = decompressor.read(len(test_data))
        # Try to read more
        result2 = decompressor.read(10)

        assert result1 == test_data
        assert result2 == b""

    def test_gzip_incremental_decompression(self):
        """Test that gzip data is decompressed incrementally"""
        # Create a larger dataset to test chunked decompression
        original_data = b"A" * 10000 + b"B" * 10000 + b"C" * 10000
        compressed_data = gzip.compress(original_data)

        decompressor = StreamingDecompressor(compressed_data)

        # Read in smaller chunks
        result = b""
        chunk_size = 1000
        while True:
            chunk = decompressor.read(chunk_size)
            if not chunk:
                break
            result += chunk

        assert result == original_data


class TestLogStream:
    """Test the LogStream class with real protobuf data"""

    def create_real_protobuf_data(self):
        """Create real protobuf data for testing"""
        # Create different telemetry messages
        depth_msg = create_test_depth_message(5.25)
        battery_msg = create_test_battery_message(0.87)

        # Create BinlogRecord entries with different timestamps
        record1 = create_real_binlog_record(1690979463, 1000, depth_msg)
        record2 = create_real_binlog_record(1690979464, 1100, battery_msg)

        return record1 + record2

    def test_logstream_with_uncompressed_data(self):
        """Test LogStream with uncompressed real protobuf data"""
        test_data = self.create_real_protobuf_data()

        # Test LogStream creation and iteration
        log_stream = LogStream(test_data, decompress=False)

        # Should be able to iterate without errors
        assert hasattr(log_stream, "__iter__")
        assert hasattr(log_stream, "__next__")

        # Get the first record
        record = next(log_stream)
        unix_timestamp, time_delta, payload_type, payload_msg = record

        # Verify the first record
        assert unix_timestamp.timestamp() == 1690979463  # Convert datetime to timestamp
        assert payload_type == bp.DepthTel
        assert payload_msg.depth.value == 5.25

    def test_logstream_with_gzip_compressed_data(self):
        """Test LogStream with gzip compressed real protobuf data"""
        test_data = self.create_real_protobuf_data()
        compressed_data = gzip.compress(test_data)

        # Test LogStream with compressed data
        log_stream = LogStream(compressed_data, decompress=True)

        # Verify it uses StreamingDecompressor
        assert isinstance(log_stream.stream, StreamingDecompressor)

        # Get the first record
        record = next(log_stream)
        unix_timestamp, time_delta, payload_type, payload_msg = record

        # Verify the first record
        assert unix_timestamp.timestamp() == 1690979463  # Convert datetime to timestamp
        assert payload_type == bp.DepthTel
        assert payload_msg.depth.value == 5.25

    def test_logstream_varint_overflow_protection(self):
        """Test that LogStream protects against malformed varint data"""
        # Create data with malformed varint (all bytes have MSB=1)
        malformed_data = b"\xff" * 15  # More than 10 bytes with MSB=1

        log_stream = LogStream(malformed_data, decompress=False)

        # Should raise StopIteration due to malformed varint protection
        with pytest.raises(StopIteration):
            next(log_stream)

    def test_logstream_empty_stream(self):
        """Test LogStream behavior with empty data"""
        log_stream = LogStream(b"", decompress=False)

        # Should raise StopIteration immediately
        with pytest.raises(StopIteration):
            next(log_stream)

    def test_logstream_io_bytesio_fallback(self):
        """Test that uncompressed data uses io.BytesIO"""
        test_data = b"uncompressed_data"
        log_stream = LogStream(test_data, decompress=False)

        # Should use io.BytesIO for uncompressed data
        assert isinstance(log_stream.stream, io.BytesIO)

    def test_logstream_handles_deserialization_errors(self):
        """Test that LogStream gracefully handles deserialization errors"""
        # Create mock data that will pass varint parsing but fail BinlogRecord deserialization
        mock_data = b"\x05hello"  # varint 5 + 5 bytes of data

        log_stream = LogStream(mock_data, decompress=False)

        # Should handle the exception and raise StopIteration
        with pytest.raises(StopIteration):
            next(log_stream)

    def test_logstream_multiple_records(self):
        """Test that LogStream can handle multiple real protobuf records"""
        test_data = self.create_real_protobuf_data()
        log_stream = LogStream(test_data, decompress=False)

        # Get both records
        record1 = next(log_stream)
        record2 = next(log_stream)

        # Verify first record (depth)
        assert record1[0].timestamp() == 1690979463  # unix_timestamp
        assert record1[2] == bp.DepthTel  # payload_type
        assert record1[3].depth.value == 5.25  # payload_msg

        # Verify second record (battery)
        assert record2[0].timestamp() == 1690979464  # unix_timestamp
        assert record2[2] == bp.BatteryTel  # payload_type
        assert abs(record2[3].battery.level - 0.87) < 0.001  # payload_msg (float precision)

        # Verify time deltas
        assert record1[1].total_seconds() == 0  # First record has delta 0
        assert record2[1].total_seconds() == 100  # Second record has delta 100

        # Should raise StopIteration for third record
        with pytest.raises(StopIteration):
            next(log_stream)


class TestLogFileParseToStream:
    """Test LogFile.parse_to_stream method"""

    def test_parse_to_stream_returns_logstream(self, mocker):
        """Test that parse_to_stream returns a LogStream instance"""
        # Create real protobuf data for testing
        depth_msg = create_test_depth_message(10.5)
        test_log_data = create_real_binlog_record(1690979463, 1000, depth_msg)

        # Mock the download method
        mock_download = mocker.patch.object(LogFile, "download", return_value=test_log_data)

        log_file = LogFile(
            name="test_log",
            is_dive=True,
            filesize=1024,
            start_time=1690979463,
            max_depth_magnitude=10,
            ip="192.168.1.101",
        )

        result = log_file.parse_to_stream()

        # Verify it returns a LogStream
        assert isinstance(result, LogStream)
        # Verify download was called with correct parameters
        mock_download.assert_called_once_with(write_to_file=False)

        # Verify we can actually get data from the stream
        record = next(result)
        unix_timestamp, time_delta, payload_type, payload_msg = record
        assert unix_timestamp.timestamp() == 1690979463
        assert payload_type == bp.DepthTel
        assert payload_msg.depth.value == 10.5
