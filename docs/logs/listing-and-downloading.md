# Logs from the drone

When the drone is powered on a new log file is created, where it stores telemetry data such as depth, temperature, and more, is created. The drone will log data as long as it is powered on. These files can be downloaded to your local system where you can plot them or use them however you see fit.

 Blunux v3.0 introduced a a modern binary log format to replace the older CSV-based logs. This updated format employs gzip compression and Google's Protocol Buffers (Protobuf) for serialization. Gzip compression reduces log file sizes, optimizing storage and data transfer. The integration of Protobuf streamlines log parsing and analysis, offering more efficient data handling.

 Every entry in the binary log is a [BinlogRecord](../protobuf-protocol.md#binlogrecord) Protobuf message, which in turn contains a unix timestamp in UTC, the monotonic timestamp (time since boot), and an Any message wrapping the Blueye telemetry message. The telemetry messages are documented in the [telemetry proto](../protobuf-protocol.md#telemetryproto).

## Listing the log files
If your drone has completed 5 dives and you do

=== "Binary logs"
    ```python
    from blueye.sdk import Drone
    myDrone = Drone()
    print(myDrone.logs)
    ```

=== "Legacy logs"
    ```python
    from blueye.sdk import Drone
    myDrone = Drone()
    print(myDrone.legacy_logs)
    ```

you should see something like the following lines be printed

=== "Binary logs"
    ```
    Name                                Time                Max depth    Size
    BYEDP000000_ea9ac92e1817a1d4_00000  07. Aug 2023 12:10  7 m          217.1 KiB
    BYEDP000000_ea9ac92e1817a1d4_00001  08. Aug 2023 12:35  20 m         1.6 MiB
    BYEDP000000_ea9ac92e1817a1d4_00002  09. Aug 2023 14:20  100 m        3.8 MiB
    BYEDP000000_ea9ac92e1817a1d4_00003  10. Aug 2023 09:15  200 m        6.5 MiB
    BYEDP000000_ea9ac92e1817a1d4_00004  11. Aug 2023 15:01  300 m        10.2 MiB

    ```
    The first part of the filename (the part before the _) is the serial number of your drone, the second part is the unique ID of the drone, and the third part is the dive number. In addition we see the start time of the dive, the maximum depth reached, as well as the size of the log file.

    Max depth is rounded down to the nearest meter for dives up to 10 meters, rounded down to the nearest 10 meters for dives up to 100 meters, and rounded down to the nearest 100 meters for deeper dives.

=== "Legacy logs"
    ```
    Name                        Time                Max depth  Size
    ea9add4d40f69d4-00000.csv   24. Oct 2018 09:40  21.05 m    6.3 MiB
    ea9add4d40f69d4-00001.csv   25. Oct 2018 10:29  21.06 m    879.2 KiB
    ea9add4d40f69d4-00002.csv   31. Oct 2018 10:05  60.69 m    8.5 MiB
    ea9add4d40f69d4-00003.csv   31. Oct 2018 12:13  41.68 m    8.4 MiB
    ea9add4d40f69d4-00004.csv   02. Nov 2018 08:59  52.52 m    7.8 MiB
    ```

    The first part of the filename (the part before the -) is the unique ID of your drone and second part is the dive number. In addition we see the start time of the dive, the maximum depth reached, as well as the size of the log file.

    The drone will by default filter out logs with a max depth below 20 cm. If you wish to list all logs you can do so by manually refreshing the log index with the `get_all_logs` parameter set to to `True`.

    ```python
    myDrone.legacy_logs.refresh_log_index(get_all_logs=True)
    ```

## Selecting a log file
There are multiple ways to select a log file from the logs index, here are some examples showing how to select by index, by name, and by slice.

!!! example "By index"
    === "Binary logs"
        ```python
        first_log: LogFile = myDrone.logs[0]
        last_log: LogFile = myDrone.logs[-1]
        ```

    === "Legacy logs"
        ```python
        first_log: LegacyLogFile = myDrone.legacy_logs[0]
        last_log: LegacyLogFile = myDrone.legacy_logs[-1]
        ```

!!! example "By name"
    === "Binary logs"
        ```python
        log: LogFile = myDrone.logs["BYEDP000000_ea9ac92e1817a1d4_00000"]
        ```

    === "Legacy logs"
        ```python
        log: LegacyLogFile = myDrone.legacy_logs["ea9add4d40f69d4-00000.csv"]
        ```

!!! example "By slice"
    === "Binary logs"
        ```python
        first_three_logs: Logs = myDrone.logs[:3]
        every_other_log: Logs = myDrone.logs[::2]
        ```

    === "Legacy logs"
        ```python
        first_three_logs: List[LegacyLogFile] = myDrone.legacy_logs[:3]
        every_other_log: List[LegacyLogFile] = myDrone.legacy_logs[::2]
        ```
## Downloading a log file to your computer
When you want to download a log file all you have to do is to call the `download()`
method on the desired log and the file will be downloaded to your current folder.

Following are some examples of how one can download log files.

!!! example "Downloading a single log file"
    === "Binary logs"
        The following will download the first log with its default name to the current folder:
        ```python
        myDrone.logs[0].download()
        ```

        If we wish to specify the name/path of the log file we can use the optional `output_path` parameter:
        ```python
        myDrone.logs[0].download(output_path="/tmp/my_log.bez")
        ```
    === "Legacy logs"
        ```python
        myDrone.legacy_logs[0].download()
        ```
        The `download()` method takes two optional parameters, `output_path` and `output_name`. These specify, respectively, which folder the log is downloaded to and what name it's stored with. So if we want to download the first log to the folder `/tmp` and name it `my_log` we can do

        ```python
        myDrone.legacy_logs[0].download(output_path="/tmp", output_name="my_log")
        ```

!!! example "Downloading multiple log files"
    Downloading multiple log files is solved by a simple Python for-loop. The example below shows how one can download the last 3 logs to the current folder:
    === "Binary logs"
        ```python
        for log in myDrone.logs[:-3]:
            log.download()
        ```
    === "Legacy logs"
        ```python
        for log in myDrone.legacy_logs[:-3]:
            log.download()
        ```

!!! example "Adding a prefix to log names"
    The example code below shows how one can add a simple prefix to all log files when downloading:

    === "Binary logs"
        ```python
        prefix = "pre_"
        for log in myDrone.logs:
            log.download(output_path=prefix+log.name+".bez")
        ```

    === "Legacy logs"
        ```python
        prefix = "pre_"
        for log in myDrone.logs:
            log.download(output_name=prefix+log.name)
        ```
