from pathlib import Path

import pandas as pd

from blueye.sdk import Drone
from blueye.sdk.logs import LogFile, LogStream


def parse_to_dataframe(log: LogFile | Path) -> pd.DataFrame:
    """Parse a log file to a pandas dataframe

    Args:
        log (LogFile | Path): The log file to parse

    Returns:
        pd.DataFrame: The dataframe with columns rt, delta, meta, message
    """
    log_bytes = b""
    if isinstance(log, Path):
        with open(log, "rb") as f:
            log_bytes = f.read()
    else:
        log_bytes = log.download(write_to_file=False)
    log_stream = LogStream(log_bytes)
    columns = ["rt", "delta", "meta", "message"]
    return pd.DataFrame.from_records(log_stream, columns=columns)


if __name__ == "__main__":
    d = Drone()
    log = d.logs[0]
    df_from_logfile = parse_to_dataframe(log)
    path = Path("/tmp/logfile.bez")
    log.download(output_path=path)
    df_from_path = parse_to_dataframe(path)
    assert df_from_logfile.equals(df_from_path)
