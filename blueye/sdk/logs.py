from datetime import datetime

import requests
import tabulate


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
    print(f"{p.logs[0]:withHeader}")
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
        self._formattedValues = [
            self.name,
            self.timestamp.strftime("%d. %b %Y %H:%M"),
            f"{self.maxdepth/1000:.2f} m",
            self._humanReadableFilesize(),
        ]

    def _humanReadableFilesize(self):
        suffix = "B"
        num = self.binsize
        for unit in ["", "Ki", "Mi"]:
            if abs(num) < 1024.0:
                return f"{num:3.1f} {unit}{suffix}"
            num /= 1024.0
        return f"{num:.1f} Gi{suffix}"

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
        if formatSpecifier == "withHeader":
            return tabulate.tabulate(
                [self], headers=["Name", "Time", "Max depth", "Size"], tablefmt="plain"
            )
        else:
            return tabulate.tabulate([self], tablefmt="plain")

    def __str__(self):
        return f"{self}"

    def __getitem__(self, item):
        return self._formattedValues[item]


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

    def __init__(self, ip="192.168.1.101", autoDownloadIndex=True):
        self.ip = ip
        if autoDownloadIndex:
            self.refreshLogIndex()
        else:
            self._logs = {}

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

    def refreshLogIndex(self):
        """Refresh the log index from the drone

        This is method is run on instantiation by default, but if you would like to
        check for new log files it can be called at any time.
        """

        listOfLogsInDictionaries = self._getListOfLogsFromDrone()
        self._logs = self._buildLogFilesFromDictionary(listOfLogsInDictionaries)

    def __getitem__(self, item):
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
