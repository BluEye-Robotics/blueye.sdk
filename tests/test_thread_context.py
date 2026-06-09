"""Regression tests guarding against attribute clashes with threading.Thread.

Python 3.14 added an internal ``self._context`` attribute to ``threading.Thread``
(a ``contextvars.Context``) which its ``_bootstrap_inner`` invokes as
``self._context.run(self.run)``. The connection thread classes used to store a
ZeroMQ context in ``self._context``, shadowing the threading attribute and
causing every worker thread to die on startup with
``AttributeError: Context has no such option: RUN``.

These tests start each thread class and assert that no exception escapes the
thread, so a future Python bump introducing a new ``Thread`` attribute clash
cannot silently reintroduce the regression.
"""

import threading
import time

import pytest

import blueye.sdk
from blueye.sdk.connection import (
    CtrlClient,
    ReqRepClient,
    TelemetryClient,
    WatchdogPublisher,
)


class OnlyIpDrone:
    _ip = "localhost"
    client_id = 1


@pytest.fixture
def captured_thread_exceptions():
    """Capture exceptions raised inside worker threads.

    Thread exceptions are reported through ``threading.excepthook`` rather than
    propagating to the thread that called ``start()``, so we install a hook to
    collect them.
    """
    exceptions = []
    original_hook = threading.excepthook
    threading.excepthook = lambda args: exceptions.append(args.exc_value)
    yield exceptions
    threading.excepthook = original_hook


@pytest.mark.parametrize(
    "thread_class",
    [WatchdogPublisher, TelemetryClient, CtrlClient, ReqRepClient],
)
def test_thread_starts_without_attribute_clash(thread_class, captured_thread_exceptions):
    thread = thread_class(parent_drone=OnlyIpDrone())
    thread.start()
    time.sleep(0.1)
    thread.stop()
    thread.join()

    assert captured_thread_exceptions == []
