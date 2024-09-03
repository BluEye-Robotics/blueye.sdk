from __future__ import annotations

import logging
import zlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterator, List, Optional, Tuple

import blueye.protocol as bp
import dateutil.parser
import proto
import requests
import tabulate
from google.protobuf.internal.decoder import _DecodeVarint as decodeVarint
from packaging import version

from .utils import deserialize_any_to_message

logger = logging.getLogger(__name__)


def human_readable_filesize(binsize: int) -> str:
    """Convert bytes to human readable string"""
    suffix = "B"
    num = binsize
    for unit in ["", "Ki", "Mi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Gi{suffix}"


def decompress_log(log: bytes) -> bytes:
    """Decompress a log file"""
    return zlib.decompressobj(wbits=zlib.MAX_WBITS | 16).decompress(log)


class LogStream:
    """Class for streaming a log

    Creates a stream from a downloaded log file. Iterate over the object to get the next log record.
    """

    def __init__(self, log: bytes, decompress: bool = True) -> Iterator[
        Tuple[
            proto.datetime_helpers.DatetimeWithNanoseconds,  # Real time clock
            timedelta,  # Time since first message
            proto.message.MessageMeta,  # Message type
            proto.message.Message,  # Message contents
        ]
    ]:
        if decompress:
            self.decompressed_log = decompress_log(log)
        else:
            self.decompressed_log = log
        self.pos = 0
        self.start_monotonic: proto.datetime_helpers.DatetimeWithNanoseconds = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.pos < len(self.decompressed_log):
            msg_size, pos_msg_start = decodeVarint(self.decompressed_log, self.pos)
            msg_data = self.decompressed_log[pos_msg_start : (pos_msg_start + msg_size)]

            if len(msg_data) < msg_size:
                raise EOFError("Not enough bytes to read message")

            self.pos = pos_msg_start + msg_size
            msg = bp.BinlogRecord.deserialize(msg_data)
            payload_type, payload_msg_deserialized = deserialize_any_to_message(msg)
            if self.start_monotonic == 0:
                self.start_monotonic = msg.clock_monotonic
            return (
                msg.unix_timestamp,
                msg.clock_monotonic - self.start_monotonic,
                payload_type,
                payload_msg_deserialized,
            )
        else:
            raise StopIteration


class LogFile:
    def __init__(
        self,
        name: str,
        is_dive: bool,
        filesize: int,
        start_time: int,
        max_depth_magnitude: int,
        ip: str,
    ):
        self.name = name
        self.is_dive = is_dive
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
            Seconds to wait for response
        * `overwrite_cache`:
            If True, the log will be downloaded even if it is already been downloaded.

        *Returns*:

        The compressed log file as a bytes object.
        """
        if self.content is None or overwrite_cache:
            self.content = requests.get(self.download_url, timeout=timeout).content
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

    def refresh_log_index(self):
        """Refresh the log index from the drone

        This is method is run on the first log access by default, but if you would like to check
        for new log files it can be called at any time.
        """
        if not self._parent_drone.connected:
            raise ConnectionError(
                "The connection to the drone is not established, try calling the connect method "
                "before retrying"
            )
        logger.debug("Refreshing log index")
        logs_endpoint = f"http://{self._parent_drone._ip}/logs"
        logs: List[dict] = requests.get(logs_endpoint).json()

        if version.parse(self._parent_drone.software_version_short) < version.parse("3.3"):
            # Extend index with dive info, sends a request for each log file so can be quite slow
            # for drones with many logs. Not necessary for Blunux >= 3.3 as dive info is included in
            # the index.
            logger.debug(f"Getting dive info for {len(logs)} logs")
            for index, log in enumerate(logs):
                dive_info = requests.get(f"{logs_endpoint}/{log['name']}/dive_info").json()
                logs[index].update(dive_info)

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
    This class is a container for a log file stored on the drone

    The drone lists the file name, max depth, start time, and file size for each log,
    and you can show this information by printing the log object, eg. on a Drone
    object called `myDrone`:

    ```
    print(myDrone.logs[0])
    ```

    or, if you want to display the header you can format the object with `with_header`:

    ```
    print(f"{myDrone.logs[0]:with_header}")
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

    def download(self, output_path=None, output_name=None, downsample_divisor=10):
        """
        Download the specified log to your local file system

        If you specify an output_path the log file will be downloaded to that directory
        instead of the current one.

        Specifying output_name will overwrite the default file name with whatever you
        have specified (be sure to include the .csv extension).

        The drone samples the log content at 10 Hz, and by default this function downsamples this
        rate to 1 Hz.
        """
        log = requests.get(self.download_path, params={"divisor": downsample_divisor}).content
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
    logfile in the list you can do `myDrone.logs[0]`, or if you want some particular log you
    can do `myDrone.logs["exampleName0001.csv"]`. You can even give it a slice, so if you want
    the last 10 logs you can do `myDrone.logs[-10:]`.
    """

    def __init__(self, parent_drone, auto_download_index=False):
        self.ip = parent_drone._ip
        self._parent_drone = parent_drone
        self.index_downloaded = False
        if auto_download_index:
            self.refresh_log_index()
        else:
            self._logs = {}

    def _get_list_of_logs_from_drone(self, get_all: bool):
        list_of_dictionaries = requests.get(
            "http://" + self.ip + "/logcsv", params={"all": True} if get_all else {}
        ).json()
        return list_of_dictionaries

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

    def refresh_log_index(self, get_all_logs=False):
        """Refresh the log index from the drone

        This is method is run on the first log access by default, but if you would like to check
        for new log files it can be called at any time.

        Pass with `get_all_logs=True` to include logs that are not classified as dives.
        """
        if not self._parent_drone.connected:
            raise ConnectionError(
                "The connection to the drone is not established, try calling the connect method "
                "before retrying"
            )
        list_of_logs_in_dictionaries = self._get_list_of_logs_from_drone(get_all_logs)
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
