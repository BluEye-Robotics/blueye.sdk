import requests
from datetime import datetime


class LogFile:
    """
    This class is a container for a log file stored on the drone

    The drone lists the file name, max depth, start time, and file size for each log,
    and you can show this information by printing the log object, eg. on a Pioneer
    object called `p`:

    ```
    print(p.logs[0])
    ```

    or, if you want to display the header you can format the object with `withHeader`:

    ```
    print(f{p.logs[0]:withHeader})
    ```

    Calling the download() method on a log object will pull the CSV (Comma Separated
    Value) file from the drone to your local filesystem.
    """

    def __init__(self, maxdepth, name, timestamp, binsize, ip):
        self.maxdepth = maxdepth
        self.name = name
        self.timestamp = datetime.fromisoformat(timestamp)
        self.binsize = binsize
        self.downloadPath = "http://" + ip + "/logcsv/" + name

    def _humanReadableFilesize(self):
        suffix = "B"
        num = self.binsize
        for unit in ["", "Ki", "Mi"]:
            if abs(num) < 1024.0:
                return "%3.1f %s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f %s%s" % (num, "Gi", suffix)

    def download(self, outputPath=None, outputName=None):
        """
        Download the specified log to your local file system

        If you specify an outputPath the log file will be downloaded to that directory
        instead of the current one.

        Specifying outputName will overwrite the default file name with whatever you
        have specified (be sure to include the .csv extension).
        """
        log = requests.get(self.downloadPath).content
        if outputPath is None:
            outputPath = "./"
        if outputName is None:
            outputName = self.name
        with open(f"{outputPath}{outputName}", "wb") as f:
            f.write(log)

    def __format__(self, formatSpecifier):
        maxDepthInMeters = f"{self.maxdepth/1000:.2f} m"
        time = self.timestamp.strftime("%d. %b %Y %H:%M")
        name_padded = f"{self.name:28}"
        time_padded = f"{time:20}"
        depth_padded = f"{maxDepthInMeters:11}"
        size_padded = f"{self._humanReadableFilesize()}"
        stringRepresentation = name_padded + time_padded + depth_padded + size_padded
        headerString = f"{'Name':28}{'Time':20}{'Max depth':11}{'Size'}\n"
        if formatSpecifier == "withHeader":
            return headerString + stringRepresentation
        else:
            return stringRepresentation

    def __str__(self):
        return f"{self}"


class Logs:
    """This class is an index of the log files stored on the drone

    To show the available logs you simply print this object, ie. if your Pioneer object
    is called `p`, you can do:

    ```
    print(p.logs)
    ```

    This will print a list of all available logs, with some of their metadata, such as
    name and maxdepth.

    You can access logfile objects either by index or by name. Eg. if you want the first
    logfile in the list you can do `p.logs[0]`, or if you want some particular log you
    can do `p.logs["exampleName0001.csv"]`. You can even give it a slice, so if you want
    the last 10 logs you can do `p.logs[:-10]`.
    """

    def __init__(self, ip="192.168.1.101"):
        self.ip = ip
        listOfLogsInDictionaries = self._getListOfLogsFromDrone()
        self._logs = self._buildLogFilesFromDictionary(listOfLogsInDictionaries)

    def _getListOfLogsFromDrone(self):
        listOfDictionaries = requests.get("http://" + self.ip + "/logcsv").json()
        return listOfDictionaries

    def _buildLogFilesFromDictionary(self, listOfLogsInDictionaries):
        loglist = {}
        for log in listOfLogsInDictionaries:
            loglist[log["name"]] = LogFile(
                log["maxdepth"], log["name"], log["timestamp"], log["binsize"], self.ip
            )
        return loglist

    def __getitem__(self, item):
        if type(item) == str:
            return self._logs[item]
        else:
            return list(self._logs.values())[item]

    def __str__(self):
        stringRepresentation = ""
        if len(self._logs) > 0:
            for index, log in enumerate(self._logs.values()):
                if index == 0:
                    stringRepresentation += f"{log:withHeader}\n"
                else:
                    stringRepresentation += f"{log}\n"
        return stringRepresentation
