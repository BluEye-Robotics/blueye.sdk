# Logs from the Pioneer

For every dive will the Pioneer will create a new comma-separated-value file where it
stores telemetry data such as depth, temperature, etc. These files can be downloaded to
your local system where you can plot them or use them however you see fit.

## Listing the log files
If your drone has completed 5 dives and you do

```python
from blueye.sdk import Pioneer

p = Pioneer()

print(p.logs)
```

you should see something like the following lines be printed

```
Name                        Time                Max depth  Size
ea9add4d40f69d4-00000.csv   24. Oct 2018 09:40  21.05 m    6.3 MiB
ea9add4d40f69d4-00001.csv   25. Oct 2018 10:29  21.06 m    879.2 KiB
ea9add4d40f69d4-00002.csv   31. Oct 2018 10:05  60.69 m    8.5 MiB
ea9add4d40f69d4-00003.csv   31. Oct 2018 12:13  41.68 m    8.4 MiB
ea9add4d40f69d4-00004.csv   02. Nov 2018 08:59  52.52 m    7.8 MiB
```

The first part of the filename (the part before the -) is the unique ID of your drone
and second part is the dive number. In addition we see the start time of the dive, the
maximum depth reached, as well as the size of the log file.

## Downloading a log file to your computer
When you want to download a log file all you have to do is to call the `download()`
method on the desired log and the file will be downloaded to your current folder.

The `download()` method takes two optional parameters, `outputPath` and `outputName`.
These specify, respectively, which folder the log is downloaded to and what name it's
stored with.

## Example: Downloading multiple log files
Downloading multiple log files is solved by a simple Python for-loop. The example below
shows how one can download the last 3 logs to the current folder:

```python
from blueye.sdk import Pioneer

p = Pioneer()

for log in p.logs[:-3]:
    log.download()
```

## Example: Adding a prefix to log names
The example code below shows how one can add a simple prefix to all log files when
downloading:

```python
from blueye.sdk import Pioneer

p = Pioneer()

prefix = "pre_"

for log in p.logs:
    log.download(outputName=prefix+log.name)
```
