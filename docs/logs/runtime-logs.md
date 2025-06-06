# Log statements from the blueye.sdk

The `blueye.sdk` package uses the standard Python logging module to log information about the SDK's operation. The log statements are useful for debugging and troubleshooting, and can be used to get a better understanding of what is happening inside the SDK.

**Note**: These logs must not be confused with the divelogs that are generated and stored on the drone. See [Listing and downloading logfiles](listing-and-downloading.md) for instructions on how to get the divelogs.

Events with severity `WARNING` or greater are printed to `sys.stderr` by default, but can be configured to be written to a file or sent to a remote server. See the [Python logging documentation](https://docs.python.org/3/library/logging.html) for more information about how to configure the logging module.

## Enabling logging with lower severity
By default, the events with severity lower than `WARNING` are muted. To enable them, you need to configure the logger to capture the logs. Here's an example of how to enable debug logs:

```python
import logging
import blueye.sdk

def enable_debug_logs():
    # Set the logger configuration
    logger = logging.getLogger(blueye.sdk.__name__)
    logger.setLevel(logging.DEBUG)

    # Define the log handler
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

    # Define the log format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Add the log handler to the logger
    logger.addHandler(handler)
```

In the example above, we import the necessary modules and create a function `enable_runtime_logs()` to enable the runtime logs. We configure the logger to capture logs with the `logging.getLogger(blueye.sdk.__name__)` statement and set the log level to `DEBUG` to capture all logs.

We also define a log handler to determine where the logs should be outputted. In this example, we use a `logging.StreamHandler()` to print the logs to the console. You can customize the log handler based on your requirements, such as writing logs to a file or sending them to a remote server.

Finally, we set the log format using `logging.Formatter()` and add the log handler to the logger using `logger.addHandler(handler)`.

## Disabling Logging

If you want to completely disable logging and prevent any logs from being captured, you can use a `NullHandler`. Here's an example:

```python
import logging
import blueye.sdk

def disable_logging():
    # Disable all logging
    logger = logging.getLogger(blueye.sdk.__name__)
    logger.addHandler(logging.NullHandler())
```

In the example above, we define a function `disable_logging()` that sets a `NullHandler` to the logger. The `NullHandler` is a special handler that essentially discards all log records, effectively disabling logging.

## Receiving logs in another terminal
Sometimes the program output can become quite cluttered if the logs are being printed inbetween the program output. In such cases, it can be useful to run the program in one terminal and then run a separate terminal to read the logs. This can be accomblished by configuring a simple TCP server to listen for log messages. Here's an example of how to do this:

```python
import logging
import logging.handlers
import socketserver
import struct


class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    def handle(self):
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack(">L", chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = self.unPickle(chunk)
            record = logging.makeLogRecord(obj)
            self.handleLogRecord(record)

    def unPickle(self, data):
        import pickle

        return pickle.loads(data)

    def handleLogRecord(self, record):
        logger = logging.getLogger(record.name)
        logger.handle(record)


class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

    def __init__(
        self,
        host="localhost",
        port=logging.handlers.DEFAULT_TCP_LOGGING_PORT,
        handler=LogRecordStreamHandler,
    ):
        socketserver.ThreadingTCPServer.__init__(self, (host, port), handler)


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s:\n    %(message)s\n"
)
tcpserver = LogRecordSocketReceiver()
print("Starting logging server...")
tcpserver.serve_forever()
```

And then we need to configure the SDKs logger to send the logs to this server.

```python
from blueye.sdk import Drone

# Set up logging
logger = logging.getLogger("blueye.sdk")
logger.setLevel(logging.INFO)
socket_handler = logging.handlers.SocketHandler(
    "localhost", logging.handlers.DEFAULT_TCP_LOGGING_PORT
)
logger.addHandler(socket_handler)

d = Drone()

# Logs from the SDK will now be sent to the logging server
```
