#
# Copyright (c) 2019-2024 Roke Manor Research Ltd
#

"""Runs the replay script (sapient_apex_replay.replay) on a background thread.

This follows the same pattern as sapient_apex_gui.core.database_thread: a plain Python Thread is
started, and results are passed back to the GUI thread via a Qt signal (which Qt automatically
delivers as a queued, thread-safe call because the receiving QObject lives on the GUI thread).

Unlike the database thread, there is no request queue here, since only one replay can run at a
time; instead this exposes start()/stop()/set_speed() methods that control state shared with the
background thread (a ThreadSafeCancelScope and a SpeedController; see sapient_apex_replay.replay).
Log messages produced by the replay script are captured via a logging.Handler and forwarded to the
GUI thread as well, so the GUI can show a live log without the replay script needing to know
anything about Qt.
"""

import logging
from dataclasses import dataclass
from threading import Thread
from typing import Optional

import trio
from PySide6 import QtCore

from sapient_apex_replay.replay import SpeedController, start_replayer
from sapient_apex_server.trio_util import ThreadSafeCancelScope

logger = logging.getLogger("apex_replay")


@dataclass
class ReplayFinished:
    """Reported via ReplayThread.state_signal when a replay run ends, for any reason."""

    error_str: Optional[str]


class _QtLogHandler(logging.Handler):
    """Logging handler that forwards formatted log records to the GUI thread via a Qt signal."""

    def __init__(self, log_signal: QtCore.SignalInstance):
        super().__init__()
        self._log_signal = log_signal

    def emit(self, record: logging.LogRecord):
        self._log_signal.emit(self.format(record))


class ReplayThread(QtCore.QObject):
    """Starts, stops, and controls the speed of a replay run happening on a background thread."""

    log_signal = QtCore.Signal(str)
    state_signal = QtCore.Signal(object)  # Actually ReplayFinished

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: Optional[Thread] = None
        self._cancel_scope: Optional[ThreadSafeCancelScope] = None
        self._speed_controller: Optional[SpeedController] = None

        log_handler = _QtLogHandler(self.log_signal)
        log_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
        logger.addHandler(log_handler)
        logger.propagate = False  # Log panel replaces the usual console output

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, config: dict):
        """Starts a replay run in the background. Do not call while is_running() is true."""
        assert not self.is_running()
        self._speed_controller = SpeedController(config["speed_multiplier"])
        self._cancel_scope = ThreadSafeCancelScope()
        self._thread = Thread(target=self._run, args=(config,), name="replay", daemon=True)
        self._thread.start()

    def stop(self):
        """Requests that the current replay run stop as soon as possible."""
        if self._cancel_scope is not None:
            self._cancel_scope.cancel()

    def set_speed(self, speed_multiplier: float):
        """Changes the speed multiplier of the current (or next) replay run."""
        if self._speed_controller is not None:
            self._speed_controller.set(speed_multiplier)

    def _run(self, config: dict):
        error_str = None
        try:
            trio.run(start_replayer, config, self._speed_controller, self._cancel_scope)
        except Exception as e:
            error_str = f"{type(e).__name__}: {e}"
            logger.error(f"Replay thread stopped unexpectedly: {error_str}")
        self.state_signal.emit(ReplayFinished(error_str))
