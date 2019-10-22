import requests
from datetime import datetime


class LogFile:
    def __init__(self, maxdepth, name, timestamp, binsize, ip):
        self.maxdepth = maxdepth
        self.name = name
        self.timestamp = datetime.fromisoformat(timestamp)
        self.binsize = binsize
        self.downloadPath = "http://" + ip + "/logcsv/" + name

    def humanReadableFilesize(self):
        suffix = "B"
        num = self.binsize
        for unit in ["", "Ki", "Mi"]:
            if abs(num) < 1024.0:
                return "%3.1f %s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f %s%s" % (num, "Gi", suffix)

    def download(self, outputPath=None, outputName=None):
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
        size_padded = f"{self.humanReadableFilesize()}"
        stringRepresentation = name_padded + time_padded + depth_padded + size_padded
        headerString = f"{'Name':28}{'Time':20}{'Max depth':11}{'Size'}\n"
        if formatSpecifier == "withHeader":
            return headerString + stringRepresentation
        else:
            return stringRepresentation

    def __str__(self):
        return f"{self}"


class Logs:
    def __init__(self, ip="192.168.1.101"):
        self.ip = ip
        listOfLogsInDictionaries = self.getListOfLogsFromDrone()
        self._logs = self.buildLogFilesFromDictionary(listOfLogsInDictionaries)

    def getListOfLogsFromDrone(self):
        listOfDictionaries = requests.get("http://" + self.ip + "/logcsv").json()
        return listOfDictionaries

    def buildLogFilesFromDictionary(self, listOfLogsInDictionaries):
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
