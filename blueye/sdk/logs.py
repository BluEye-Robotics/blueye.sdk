from __future__ import annotations

import io
import logging
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Dict, Iterator, List, Optional, Tuple, Union

import blueye.protocol as bp
import dateutil.parser
import proto
import requests
import tabulate
from google.protobuf.internal.decoder import _DecodeVarint as decodeVarint
from packaging import version

from .utils import deserialize_any_to_message

logger = logging.getLogger(__name__)

#: Seconds to wait for the drone to answer a log index or dive info request. This is the
#: `requests` timeout: the time to connect, and then the time between bytes.
HTTP_TIMEOUT = 10


def human_readable_filesize(binsize: int) -> str:
    """Convert bytes to human readable string"""
    suffix = "B"
    num = binsize
    for unit in ["", "Ki", "Mi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Gi{suffix}"


def is_gzip_compressed(data: bytes) -> bool:
    """Check if data is gzip compressed by looking at the magic header bytes"""
    return len(data) >= 2 and data[0] == 0x1F and data[1] == 0x8B


class StreamingDecompressor:
    """A streaming decompressor that handles gzip data incrementally"""

    def __init__(self, compressed_data: bytes):
        self.compressed_data = compressed_data
        self.compressed_pos = 0
        self.decompressor = None
        self.decompressed_buffer = bytearray()
        self.eof = False

        if is_gzip_compressed(compressed_data):
            # Initialize zlib decompressor for gzip data
            self.decompressor = zlib.decompressobj(wbits=zlib.MAX_WBITS | 16)
        else:
            # Data is not compressed
            self.decompressed_buffer = bytearray(compressed_data)
            self.eof = True

    def read(self, size: int) -> bytes:
        """Read up to size bytes from the decompressed stream"""
        if self.eof and len(self.decompressed_buffer) == 0:
            return b""

        # If we need more decompressed data and we're not at EOF
        while len(self.decompressed_buffer) < size and not self.eof:
            # Read a chunk from compressed data
            chunk_size = min(8192, len(self.compressed_data) - self.compressed_pos)
            if chunk_size == 0:
                # No more compressed data
                if self.decompressor:
                    # Finalize decompression. This can fail on corrupted data.
                    try:
                        final_data = self.decompressor.flush()
                        self.decompressed_buffer.extend(final_data)
                    except zlib.error as e:
                        logger.warning(
                            f"Decompression flush failed, likely due to corrupted data: {e}"
                        )
                    except (MemoryError, OverflowError) as e:
                        logger.error(f"Decompression flush failed due to resource limits: {e}")
                    except Exception as e:
                        logger.error(f"Unexpected error during decompression flush: {e}")
                self.eof = True
                break

            chunk = self.compressed_data[self.compressed_pos : self.compressed_pos + chunk_size]
            self.compressed_pos += chunk_size

            if self.decompressor:
                try:
                    decompressed_chunk = self.decompressor.decompress(chunk)
                    self.decompressed_buffer.extend(decompressed_chunk)
                except zlib.error as e:
                    # If decompression fails, we're probably done. This can happen with
                    # truncated or corrupted files.
                    logger.warning(f"Decompression of chunk failed: {e}")
                    self.eof = True
                    break
                except (MemoryError, OverflowError) as e:
                    logger.error(f"Decompression failed due to resource limits: {e}")
                    self.eof = True
                    break
                except Exception as e:
                    logger.error(f"Unexpected error during decompression: {e}")
                    self.eof = True
                    break

        # Return requested amount of data
        result_size = min(size, len(self.decompressed_buffer))
        result = bytes(self.decompressed_buffer[:result_size])
        self.decompressed_buffer = self.decompressed_buffer[result_size:]

        return result


class LogStream:
    """Class for streaming a log

    Creates a stream from a downloaded log file. Iterate over the object to get the next log
    record as a tuple of

    * the wall clock time of the record (`DatetimeWithNanoseconds`, UTC),
    * the time since the first record in the log (`timedelta`),
    * the message type, eg. `bp.DepthTel`, and
    * the message itself.

    A log can hold types this SDK does not know, for instance when the drone runs a newer
    release than the installed blueye.protocol package. By default those records are skipped:
    the first one of each type logs a warning, and all of them are counted per type URL in
    `unknown_types`. Pass `include_unknown=True` to get them as
    `(time, time since first record, type URL, raw payload bytes)` tuples instead, where the
    type URL is a string such as `"type.googleapis.com/blueye.protocol.PowerCanisterTel"`.
    """

    def __init__(
        self, log: bytes, decompress: bool = True, include_unknown: bool = False
    ) -> Iterator[
        Tuple[
            proto.datetime_helpers.DatetimeWithNanoseconds,  # Real time clock
            timedelta,  # Time since first message
            Union[type, str],  # Message type, or its type URL if the SDK does not know it
            Union[proto.message.Message, bytes],  # Message contents, or the raw payload
        ]
    ]:
        if decompress:
            self.stream = StreamingDecompressor(log)
        else:
            self.stream = io.BytesIO(log)

        self.include_unknown = include_unknown
        #: Type URL -> number of records in the stream so far that could not be decoded
        self.unknown_types: Dict[str, int] = {}
        self.start_monotonic: proto.datetime_helpers.DatetimeWithNanoseconds = 0
        self._summary_logged = False

    def __iter__(self):
        return self

    def _read_record(self) -> bytes:
        """Read the next length-prefixed record, or raise StopIteration at the end"""
        try:
            # Read bytes one by one until we have a complete varint
            varint_bytes = bytearray()
            while True:
                byte_data = self.stream.read(1)  # Read one byte at a time
                if not byte_data:
                    raise StopIteration  # End of stream
                varint_bytes.append(byte_data[0])  # Add byte to our varint buffer

                # Check if this is the last byte of the varint (MSB is 0)
                if byte_data[0] < 0x80:  # 0x80 = 128 = 10000000 binary
                    break  # MSB is 0, so we're done

                # Prevent infinite loop with malformed data
                if len(varint_bytes) > 10:  # Max varint size for 64-bit
                    logger.error("Malformed varint detected")
                    raise StopIteration

            # Use Google's protobuf decoder to decode the varint
            msg_size, _ = decodeVarint(bytes(varint_bytes), 0)

            # Read the message data
            msg_data = self.stream.read(msg_size)
            if len(msg_data) < msg_size:
                raise StopIteration
            return msg_data

        except (ValueError, IOError) as e:
            logger.error(f"Error reading log stream: {e}")
            raise StopIteration

    def _end_of_stream(self):
        """Log the unknown-type summary once, then stop the iteration"""
        skipped = sum(self.unknown_types.values())
        if skipped and not self.include_unknown and not self._summary_logged:
            self._summary_logged = True
            logger.info(
                f"Skipped {skipped} records of {len(self.unknown_types)} message types this SDK "
                f"cannot decode: {', '.join(sorted(self.unknown_types))}"
            )
        raise StopIteration

    def _count_unknown(self, type_url: str, error: Exception):
        first = type_url not in self.unknown_types
        self.unknown_types[type_url] = self.unknown_types.get(type_url, 0) + 1
        if not first:
            return
        if self.include_unknown:
            logger.debug(f"Cannot decode {type_url}, passing the raw payload through: {error}")
        else:
            logger.warning(
                f"Skipping records of type {type_url}, which this SDK cannot decode: {error}. "
                "Further records of this type are counted in LogStream.unknown_types without "
                "a log line."
            )

    def __next__(self):
        # A loop rather than a recursive call, so a long run of records the SDK cannot decode
        # does not exhaust the interpreter stack.
        while True:
            try:
                msg_data = self._read_record()
            except StopIteration:
                self._end_of_stream()

            try:
                msg = bp.BinlogRecord.deserialize(msg_data)
            except Exception as e:
                logger.error(f"Failed to deserialize log record: {e}")
                continue
            if msg.clock_monotonic is None or msg.unix_timestamp is None:
                logger.error("Skipping log record without timestamps")
                continue

            if self.start_monotonic == 0:
                self.start_monotonic = msg.clock_monotonic
            delta = msg.clock_monotonic - self.start_monotonic

            try:
                payload_type, payload_msg_deserialized = deserialize_any_to_message(msg.payload)
            except Exception as e:
                type_url = msg.payload.type_url
                self._count_unknown(type_url, e)
                if self.include_unknown:
                    return (msg.unix_timestamp, delta, type_url, msg.payload.value)
                continue

            return (msg.unix_timestamp, delta, payload_type, payload_msg_deserialized)


class LogFile:
    """A binary log stored on the drone

    The drone opens a new log at every power-on and keeps writing to it until it is powered
    off, so the log for the current power cycle is always `is_open`. The drone flushes an
    open log to disk every 10 seconds, so downloading it gives a snapshot that stops
    mid-record. `download()` does not cache open logs, and `blueye logs download --latest`
    skips them.
    """

    def __init__(
        self,
        name: str,
        is_dive: bool,
        filesize: int,
        start_time: int,
        max_depth_magnitude: int,
        ip: str,
        is_open: bool = False,
    ):
        self.name = name
        self.is_dive = is_dive
        self.is_open = is_open
        self.filesize = filesize
        self.start_time: datetime = datetime.fromtimestamp(start_time, tz=timezone.utc)
        self.max_depth_magnitude = max_depth_magnitude
        self.download_url = f"http://{ip}/logs/{self.name}/binlog"
        self.content = None
        self._formatted_values = [
            self.name,
            self.start_time.strftime("%d. %b %Y %H:%M"),
            f"{self.max_depth_magnitude} m",
            human_readable_filesize(self.filesize),
        ]

    def download(
        self,
        output_path: Optional[Path | str] = None,
        write_to_file: bool = True,
        timeout: float = 1,
        overwrite_cache: bool = False,
    ) -> bytes:
        """Download a log file from the drone

        *Arguments*:

        * `output_path`:
            Path to write the log file to. If `None`, the log will be written to the
            current working directory. If the path is a directory, the log will be
            downloaded to that directory with its original name. Else the log will be
            downloaded to the specified path.
        * `write_to_file`:
            If True, the log will be written to the specified path. If False, the
            log will only be returned as a bytes object.
        * `timeout`:
            Seconds to wait for the drone to connect, and then between bytes of the response.
            This is the `requests` timeout, so it does not limit the total download time.
        * `overwrite_cache`:
            If True, the log will be downloaded even if it is already been downloaded.
            Open logs (`is_open`) are always downloaded again, since the drone is still
            writing to them.

        *Returns*:

        The compressed log file as a bytes object.

        *Raises*:

        `requests.HTTPError` if the drone answers with an error status, and
        `requests.ConnectionError` or `requests.Timeout` if it does not answer.
        """
        if self.is_open:
            logger.warning(
                f"Log {self.name} is still being written by the drone, so the download is a "
                "snapshot that stops mid-record"
            )
        if self.content is None or overwrite_cache or self.is_open:
            response = requests.get(self.download_url, timeout=timeout)
            response.raise_for_status()
            self.content = response.content
        if write_to_file:
            if output_path is None:
                output_path = Path(f"{self.name}.bez")
            else:
                if type(output_path) == str:
                    output_path = Path(output_path)
                if output_path.is_dir():
                    output_path = output_path.joinpath(f"{self.name}.bez")
            with open(output_path, "wb") as f:
                f.write(self.content)
        return self.content

    def parse_to_stream(self) -> LogStream:
        """Parse the log file to a stream

        Will download the log if it is not already downloaded.

        *Returns*:

        A `LogStream` object
        """
        return LogStream(self.download(write_to_file=False))

    def __format__(self, format_specifier):
        if format_specifier == "with_header":
            return tabulate.tabulate(
                [self], headers=["Name", "Time", "Max depth", "Size"], tablefmt="plain"
            )
        else:
            return tabulate.tabulate([self], tablefmt="plain")

    def __str__(self):
        return f"{self}"

    def __getitem__(self, item):
        return self._formatted_values[item]


class Logs:
    def __init__(self, parent_drone, auto_download_index=False):
        self._parent_drone = parent_drone
        self.auto_download_index = auto_download_index
        self.index_downloaded = False
        self._logs = {}
        if auto_download_index:
            self.refresh_log_index()

    def refresh_log_index(self, timeout: float = HTTP_TIMEOUT):
        """Refresh the log index from the drone

        This is method is run on the first log access by default, but if you would like to check
        for new log files it can be called at any time.

        `timeout` is the seconds to wait for each request to the drone. Raises
        `requests.HTTPError` if the drone answers with an error status.
        """
        if not self._parent_drone.connected:
            raise ConnectionError(
                "The connection to the drone is not established, try calling the connect method "
                "before retrying"
            )
        logger.debug("Refreshing log index")
        logs_endpoint = f"http://{self._parent_drone._ip}/logs"
        response = requests.get(logs_endpoint, timeout=timeout)
        response.raise_for_status()
        logs: List[dict] = response.json()

        if version.parse(self._parent_drone.software_version_short) < version.parse("3.3"):
            # Extend index with dive info, sends a request for each log file so can be quite slow
            # for drones with many logs. Not necessary for Blunux >= 3.3 as dive info is included in
            # the index.
            logger.debug(f"Getting dive info for {len(logs)} logs")
            for index, log in enumerate(logs):
                response = requests.get(f"{logs_endpoint}/{log['name']}/dive_info", timeout=timeout)
                response.raise_for_status()
                logs[index].update(response.json())

        # Instantiate log objects for each log
        logger.debug(f"Creating log objects for {len(logs)} logs")
        for log in logs:
            if log["has_binlog"]:
                self._logs[log["name"]] = LogFile(
                    log["name"],
                    log["is_dive"],
                    log["binlog_size"],
                    log["start_time"],
                    log["max_depth_magnitude"],
                    self._parent_drone._ip,
                    is_open=log.get("is_open", False),
                )
            else:
                logger.info(f"Log {log['name']} does not have a binlog, ignoring")
        self.index_downloaded = True

    def __len__(self):
        if not self.index_downloaded:
            self.refresh_log_index()
        return len(self._logs)

    def __getitem__(self, item):
        if not self.index_downloaded:
            self.refresh_log_index()
        if type(item) == str:
            try:
                return self._logs[item]
            except KeyError:
                raise KeyError(f"A log with the name '{item}' does not exist")
        elif isinstance(item, slice):
            logs_slice = Logs(self._parent_drone)
            for log in list(self._logs.values())[item]:
                logs_slice._logs[log.name] = log
            logs_slice.index_downloaded = True
            return logs_slice
        else:
            try:
                return list(self._logs.values())[item]
            except IndexError:
                raise IndexError(
                    f"Tried to access log nr {item}, "
                    + f"but there are only {len(self._logs.values())} logs available"
                )

    def __str__(self):
        return tabulate.tabulate(
            self, headers=["Name", "Time", "Max depth", "Size"], tablefmt="plain"
        )

    def filter(self, filter_func: Callable[[LogFile], bool]) -> Logs:
        """Return a new Logs object with only those matching the filter

        Eg. to get logs classified as a dive:
        ```
        dive_logs = myDrone.logs.filter(lambda log: log.is_dive)
        ```

        or to get all logs with a max depth greater than 10m:
        ```
        deep_logs = myDrone.logs.filter(lambda log: log.max_depth_magnitude > 10)
        ```
        """
        if not self.index_downloaded:
            self.refresh_log_index()
        filtered_logs = Logs(self._parent_drone)
        filtered_logs.index_downloaded = True
        for log in self:
            if filter_func(log):
                filtered_logs._logs[log.name] = log
        return filtered_logs


class LegacyLogFile:
    """
    This class is a container for a legacy CSV log file stored on the drone

    The drone lists the file name, max depth, start time, and file size for each log,
    and you can show this information by printing the log object, eg. on a Drone
    object called `myDrone`:

    ```
    print(myDrone.legacy_logs[0])
    ```

    or, if you want to display the header you can format the object with `with_header`:

    ```
    print(f"{myDrone.legacy_logs[0]:with_header}")
    ```

    Calling the download() method on a log object will pull the CSV (Comma Separated
    Value) file from the drone to your local filesystem.
    """

    def __init__(self, maxdepth, name, timestamp, binsize, ip):
        self.maxdepth = maxdepth
        self.name = name
        self.timestamp: datetime = dateutil.parser.isoparse(timestamp)
        self.binsize = binsize
        self.download_path = "http://" + ip + "/logcsv/" + name
        self._formatted_values = [
            self.name,
            self.timestamp.strftime("%d. %b %Y %H:%M"),
            f"{self.maxdepth/1000:.2f} m",
            human_readable_filesize(self.binsize),
        ]

    def download(
        self, output_path=None, output_name=None, downsample_divisor=10, timeout=HTTP_TIMEOUT
    ):
        """
        Download the specified log to your local file system

        If you specify an output_path the log file will be downloaded to that directory
        instead of the current one.

        Specifying output_name will overwrite the default file name with whatever you
        have specified (be sure to include the .csv extension).

        The drone samples the log content at 10 Hz, and by default this function downsamples this
        rate to 1 Hz.

        `timeout` is the seconds to wait for the drone to connect and then between bytes.
        Raises `requests.HTTPError` if the drone answers with an error status.
        """
        response = requests.get(
            self.download_path, params={"divisor": downsample_divisor}, timeout=timeout
        )
        response.raise_for_status()
        log = response.content
        if output_path is None:
            output_path = "./"
        if output_name is None:
            output_name = self.name
        with open(f"{output_path}{output_name}", "wb") as f:
            f.write(log)

    def __format__(self, format_specifier):
        if format_specifier == "with_header":
            return tabulate.tabulate(
                [self], headers=["Name", "Time", "Max depth", "Size"], tablefmt="plain"
            )
        else:
            return tabulate.tabulate([self], tablefmt="plain")

    def __str__(self):
        return f"{self}"

    def __getitem__(self, item):
        return self._formatted_values[item]


class LegacyLogs:
    """This class is an index of the legacy csv log files stored on the drone

    To show the available logs you simply print this object, ie. if your Drone object
    is called `myDrone`, you can do:

    ```
    print(myDrone.legacy_logs)
    ```

    This will print a list of all available logs, with some of their metadata, such as
    name and maxdepth.

    You can access logfile objects either by index or by name. Eg. if you want the first
    logfile in the list you can do `myDrone.legacy_logs[0]`, or if you want some particular
    log you can do `myDrone.legacy_logs["exampleName0001.csv"]`. You can even give it a
    slice, so if you want the last 10 logs you can do `myDrone.legacy_logs[-10:]`.
    """

    def __init__(self, parent_drone, auto_download_index=False):
        self.ip = parent_drone._ip
        self._parent_drone = parent_drone
        self.index_downloaded = False
        if auto_download_index:
            self.refresh_log_index()
        else:
            self._logs = {}

    def _get_list_of_logs_from_drone(self, get_all: bool, timeout: float = HTTP_TIMEOUT):
        response = requests.get(
            "http://" + self.ip + "/logcsv",
            params={"all": True} if get_all else {},
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()

    def _build_log_files_from_dictionary(self, list_of_logs_in_dictionaries):
        loglist = {}
        for log in list_of_logs_in_dictionaries:
            try:
                loglist[log["name"]] = LegacyLogFile(
                    log["maxdepth"], log["name"], log["timestamp"], log["binsize"], self.ip
                )
            except dateutil.parser.ParserError:
                logger.warning(
                    f"Could not parse timestamp for log {log['name']}, skipping this log file"
                )
        return loglist

    def refresh_log_index(self, get_all_logs=False, timeout: float = HTTP_TIMEOUT):
        """Refresh the log index from the drone

        This is method is run on the first log access by default, but if you would like to check
        for new log files it can be called at any time.

        Pass with `get_all_logs=True` to include logs that are not classified as dives.
        `timeout` is the seconds to wait for the drone to answer.
        """
        if not self._parent_drone.connected:
            raise ConnectionError(
                "The connection to the drone is not established, try calling the connect method "
                "before retrying"
            )
        list_of_logs_in_dictionaries = self._get_list_of_logs_from_drone(get_all_logs, timeout)
        self._logs = self._build_log_files_from_dictionary(list_of_logs_in_dictionaries)
        self.index_downloaded = True

    def __len__(self):
        if not self.index_downloaded:
            self.refresh_log_index()
        return len(self._logs)

    def __getitem__(self, item):
        if not self.index_downloaded:
            self.refresh_log_index()
        if type(item) == str:
            try:
                return self._logs[item]
            except KeyError:
                raise KeyError(f"A log with the name '{item}' does not exist")
        else:
            try:
                return list(self._logs.values())[item]
            except IndexError:
                raise IndexError(
                    f"Tried to access log nr {item}, "
                    + f"but there are only {len(self._logs.values())} logs available"
                )

    def __str__(self):
        return tabulate.tabulate(
            self, headers=["Name", "Time", "Max depth", "Size"], tablefmt="plain"
        )
