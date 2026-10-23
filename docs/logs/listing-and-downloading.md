# Logs from the drone

The drone opens a new log file every time it is powered on and writes telemetry such as depth, temperature and attitude to it until it is powered off. These files can be downloaded to your computer, where you can plot them or process them however you see fit.

Blunux 3.0 introduced a binary log format that replaced the older CSV logs. A binary log is a gzip-compressed sequence of length-prefixed [BinlogRecord][blueye.protocol.types.message_formats.BinlogRecord] Protobuf messages. Each record holds a unix timestamp in UTC, the monotonic timestamp (time since boot), and an Any message wrapping a Blueye protocol message, most often a telemetry message. The telemetry messages are documented in the [telemetry proto][blueye.protocol.types.telemetry]. Drones on Blunux older than 3.0 are covered at the [end of this page](#legacy-csv-logs-blunux-older-than-30).

## From the command line

The binary logs are also available through the [`blueye` CLI](../cli.md), which is
installed with the SDK and connects to the drone as an observer — taking no control:

```shell
blueye logs list                       # table of logs on the drone
blueye logs download --latest 1        # newest finished log to the current directory
blueye logs download --latest 1 --mcap # ...and convert it for Foxglove
blueye logs download --latest 1 --dives-only  # newest dive, skipping power-on logs
blueye logs download BYEDP000000_ea9ac92e1817a1d4_00002 -o ~/dives
blueye logs                            # interactive: pick logs to download
```

## Connecting

Logs are read over HTTP, so you do not need control of the drone to work with them. Connect as an observer, which leaves the pilot in control and still lets you list and download logs:

```python
from blueye.sdk import Drone

myDrone = Drone(connect_as_observer=True)
```

The examples below use this `myDrone` object.

## Listing the log files

If your drone has completed 5 dives and you do

```python
print(myDrone.logs)
```

you should see something like the following lines be printed

```
Name                                Time                Max depth    Size
BYEDP000000_ea9ac92e1817a1d4_00000  07. Aug 2023 12:10  7 m          217.1 KiB
BYEDP000000_ea9ac92e1817a1d4_00001  08. Aug 2023 12:35  20 m         1.6 MiB
BYEDP000000_ea9ac92e1817a1d4_00002  09. Aug 2023 14:20  100 m        3.8 MiB
BYEDP000000_ea9ac92e1817a1d4_00003  10. Aug 2023 09:15  200 m        6.5 MiB
BYEDP000000_ea9ac92e1817a1d4_00004  11. Aug 2023 15:01  300 m        10.2 MiB
```

The first part of the filename (the part before the `_`) is the serial number of your drone, the second part is the unique ID of the drone, and the third part is the log number. In addition we see the start time of the log, the maximum depth reached, and the size of the log file.

Max depth is rounded down to the nearest meter for dives up to 10 meters, rounded down to the nearest 10 meters for dives up to 100 meters, and rounded down to the nearest 100 meters for deeper dives.

The index is fetched from the drone the first time you touch `myDrone.logs`. To pick up logs that were created after that, refresh it:

```python
myDrone.logs.refresh_log_index()
```

## What a log file knows about itself

Each entry in the index is a [`LogFile`][blueye.sdk.logs.LogFile] with these attributes:

| Attribute             | Type       | Meaning                                                                                         |
| --------------------- | ---------- | ----------------------------------------------------------------------------------------------- |
| `name`                | `str`      | The log name, as listed above, without the `.bez` extension.                                    |
| `start_time`          | `datetime` | When the log was started, in UTC.                                                               |
| `is_dive`             | `bool`     | `True` if the drone went deeper than 25 cm or an auto function was used during the log.        |
| `is_open`             | `bool`     | `True` if the drone is still writing to the log. See [Limits](#limits).                         |
| `filesize`            | `int`      | Size of the compressed log on the drone, in bytes.                                              |
| `max_depth_magnitude` | `int`      | Deepest point of the log in meters, rounded down as described above.                            |
| `download_url`        | `str`      | The URL the log is downloaded from.                                                             |
| `content`             | `bytes`    | The downloaded, still compressed, log, or `None` until `download()` has been called.           |

## Selecting a log file

There are multiple ways to select a log file from the logs index, here are some examples showing how to select by index, by name, and by slice.

/// admonition | By index
    type: example

```python
first_log: LogFile = myDrone.logs[0]
last_log: LogFile = myDrone.logs[-1]
```
///

/// admonition | By name
    type: example

```python
log: LogFile = myDrone.logs["BYEDP000000_ea9ac92e1817a1d4_00000"]
```
///

/// admonition | By slice
    type: example

```python
first_three_logs: Logs = myDrone.logs[:3]
last_three_logs: Logs = myDrone.logs[-3:]
every_other_log: Logs = myDrone.logs[::2]
```
///

## Filtering

[`Logs.filter`][blueye.sdk.logs.Logs.filter] takes a function that gets a `LogFile` and returns a new `Logs` index with the entries the function accepted. Some examples:

```python
dive_logs = myDrone.logs.filter(lambda log: log.is_dive)
deep_logs = myDrone.logs.filter(lambda log: log.max_depth_magnitude >= 50)
finished_logs = myDrone.logs.filter(lambda log: not log.is_open)
```

The filtered index can be indexed, sliced and iterated like `myDrone.logs`:

```python
latest_dive = myDrone.logs.filter(lambda log: log.is_dive and not log.is_open)[-1]
```

## Downloading a log file to your computer

When you want to download a log file all you have to do is to call the `download()`
method on the desired log and the file will be downloaded to your current folder.

Following are some examples of how one can download log files.

/// admonition | Downloading a single log file
    type: example
The following will download the first log with its default name to the current folder:
```python
myDrone.logs[0].download()
```

If we wish to specify the name/path of the log file we can use the optional `output_path` parameter:
```python
myDrone.logs[0].download(output_path="/tmp/my_log.bez")
```

If `output_path` is a directory, the log is saved there with its default name.
///

/// admonition | Downloading multiple log files
    type: example
Downloading multiple log files is solved by a simple Python for-loop. The example below shows how one can download the last 3 logs to the current folder:
```python
for log in myDrone.logs[-3:]:
    log.download()
```
///

/// admonition | Adding a prefix to log names
    type: example
The example code below shows how one can add a simple prefix to all log files when downloading:

```python
prefix = "pre_"
for log in myDrone.logs:
    log.download(output_path=prefix + log.name + ".bez")
```
///

`download()` keeps the downloaded bytes in `log.content` and returns them, so calling it again on the same `LogFile` does not contact the drone unless you pass `overwrite_cache=True`. Pass `write_to_file=False` to get the bytes without saving a file.

## Streaming the records

[`LogFile.parse_to_stream()`][blueye.sdk.logs.LogFile.parse_to_stream] downloads the log if needed and returns a [`LogStream`][blueye.sdk.logs.LogStream], an iterator that decompresses and decodes the log one record at a time. Each record is a tuple of four values:

| Position | Type                      | Meaning                                                                                        |
| -------- | ------------------------- | ---------------------------------------------------------------------------------------------- |
| 0        | `DatetimeWithNanoseconds` | The drone's wall clock when the record was written, in UTC.                                    |
| 1        | `timedelta`               | Time since the first record in the log, from the drone's monotonic clock.                      |
| 2        | message type              | The protocol class of the message, for instance `bp.DepthTel`.                                 |
| 3        | message                   | The decoded message.                                                                           |

```python
import blueye.protocol as bp

for wall_time, since_start, message_type, message in myDrone.logs[0].parse_to_stream():
    if message_type is bp.DepthTel:
        print(f"{since_start}  {message.depth.value:.2f} m")
```

The wall clock is only as good as the drone's clock. The drone does not keep time across power cycles; the SDK and the Blueye app set it when they take control, so the records before that carry a wrong date. The monotonic delta is always continuous. `LogStream` also accepts the bytes of a log that is already on disk:

```python
from blueye.sdk.logs import LogStream

with open("BYEDP000000_ea9ac92e1817a1d4_00000.bez", "rb") as f:
    stream = LogStream(f.read())
```

[Plotting log files](plotting.md) shows how to load a stream into a pandas DataFrame, and the [Foxglove page](foxglove-bez-to-mcap.md) how to convert one for playback.

### Message types this SDK does not know

The drone logs every message type its firmware knows, so a drone on a newer release than your `blueye.protocol` package can produce records the SDK has no class for. `LogStream` skips those by default: the first record of each type logs a warning, and all of them are counted per type URL in `stream.unknown_types`. To get them anyway, pass `include_unknown=True` and the stream yields them as `(wall_time, since_start, type_url, raw_bytes)` tuples, where `type_url` is a string such as `"type.googleapis.com/blueye.protocol.PowerCanisterTel"` and `raw_bytes` is the undecoded payload. Upgrading `blueye.protocol` is the way to decode them.

## Limits

- **One log is always open.** The drone writes a new log from power-on to power-off, so the log for the current power cycle has `is_open` set while you are connected. The drone flushes it to disk every 10 seconds, so downloading it gives a snapshot that stops mid-record. `download()` warns about this and does not cache open logs. The CLI's `--latest` skips them.
- **Logs stop after 10 hours.** The drone closes a log after 600 minutes even if it stays powered on. Nothing after that is logged until the next power cycle.
- **Download timeout.** `download(timeout=...)` defaults to 1 second. This is the `requests` timeout: the time allowed to connect, and then between bytes, so a large log is not cut off as long as the drone keeps sending. On a slow link, raise it.
- **Index timeout.** `refresh_log_index(timeout=...)` defaults to 10 seconds per request. Drones on Blunux older than 3.3 need one extra request per log to fill in the dive info, so the first listing on a drone with many logs takes a while.
- **Error responses raise.** A `requests.HTTPError` is raised if the drone answers a log request with an error status, rather than saving the error page as a log.

## Legacy CSV logs (Blunux older than 3.0)

Drones on Blunux older than 3.0 store CSV logs instead, available as `myDrone.legacy_logs`. The format is described on the [legacy log file format](legacy-log-file-format.md) page. The index works like the binary one, with a few differences.

/// details | Listing, selecting and downloading legacy logs

```python
print(myDrone.legacy_logs)
```

```
Name                        Time                Max depth  Size
ea9add4d40f69d4-00000.csv   24. Oct 2018 09:40  21.05 m    6.3 MiB
ea9add4d40f69d4-00001.csv   25. Oct 2018 10:29  21.06 m    879.2 KiB
ea9add4d40f69d4-00002.csv   31. Oct 2018 10:05  60.69 m    8.5 MiB
ea9add4d40f69d4-00003.csv   31. Oct 2018 12:13  41.68 m    8.4 MiB
ea9add4d40f69d4-00004.csv   02. Nov 2018 08:59  52.52 m    7.8 MiB
```

The first part of the filename (the part before the `-`) is the unique ID of your drone and the second part is the dive number.

The drone leaves out logs with a max depth below 20 cm. To list them as well, refresh the index with `get_all_logs=True`:

```python
myDrone.legacy_logs.refresh_log_index(get_all_logs=True)
```

Select by index, by name or by slice. Slicing a legacy index gives a list rather than a new index:

```python
first_log: LegacyLogFile = myDrone.legacy_logs[0]
log: LegacyLogFile = myDrone.legacy_logs["ea9add4d40f69d4-00000.csv"]
first_three_logs: List[LegacyLogFile] = myDrone.legacy_logs[:3]
```

`download()` takes `output_path`, the directory to save to, and `output_name`, the file name to use. The drone samples at 10 Hz, and `downsample_divisor` (default 10) picks every n-th sample:

```python
myDrone.legacy_logs[0].download()
myDrone.legacy_logs[0].download(output_path="/tmp/", output_name="my_log.csv")

for log in myDrone.legacy_logs[-3:]:
    log.download()

prefix = "pre_"
for log in myDrone.legacy_logs:
    log.download(output_name=prefix + log.name)
```
///
