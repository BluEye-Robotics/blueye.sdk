"""Shared helpers for built-in commands that talk to the drone."""

from __future__ import annotations

import argparse
import logging

from ..errors import CliError

logger = logging.getLogger(__name__)


def drone_options_parser(timeout_default: float = 5.0) -> argparse.ArgumentParser:
    """Build the parent parser carrying the common drone connection options."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--drone-ip", default="192.168.1.101", help="Drone address (default: %(default)s)"
    )
    common.add_argument(
        "--timeout", type=float, default=timeout_default, help="Request timeout in seconds"
    )
    return common


def friendly_errors(action):
    """Run an action, translating transport/API failures into CliErrors."""
    import requests

    try:
        return action()
    except (
        ConnectionError,  # Raised by Drone.connect()/_update_drone_info.
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
    ) as error:
        raise CliError(
            "Could not reach the drone — is it connected? (Use --drone-ip if it is not "
            "at the default address.)"
        ) from error
    except requests.exceptions.HTTPError as error:
        raise CliError(str(error)) from error
