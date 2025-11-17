import logging
import logging.handlers
import socketserver
import struct

import click


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


@click.command(name="log-server")
@click.option("--host", default="localhost", help="Address to host the logging server on.")
@click.option(
    "--port",
    default=logging.handlers.DEFAULT_TCP_LOGGING_PORT,
    help="Port to host the logging server on.",
)
@click.option(
    "--level",
    default="DEBUG",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False),
    help="Logging level for the server.",
)
@click.option(
    "--format",
    "log_format",
    default="%(asctime)s - %(name)s - %(levelname)s:\n    %(message)s\n",
    help="Logging format string.",
)
def main(host, port, level, log_format):
    """
    Starts a TCP logging server that receives log records from remote sources.
    """
    # Convert level string to logging level constant
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")

    logging.basicConfig(level=numeric_level, format=log_format)

    tcpserver = LogRecordSocketReceiver(host=host, port=port)
    click.echo(f"Starting logging server on {host}:{port} with level {level}...")
    click.echo("\nTo connect to this log server from your Python code, use:")
    click.echo("import logging")
    click.echo("import logging.handlers")
    click.echo("")
    click.echo("logger = logging.getLogger('blueye.sdk')")
    click.echo(f"logger.setLevel(logging.{level.upper()})")
    click.echo(f"socket_handler = logging.handlers.SocketHandler('{host}', {port})")
    click.echo("logger.addHandler(socket_handler)")
    click.echo("")
    tcpserver.serve_forever()
