#
# Copyright (c) 2019-2024 Roke Manor Research Ltd
#

"""Main window of the Apex Replay GUI.

Lets the user pick a recorded SQLite database, then start, stop, and change the speed of replaying
it back out over the network, using sapient_apex_replay.replay under the hood (see ReplayThread).
"""

import sys
from pathlib import Path

from PySide6.QtCore import QMargins, QSize, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from sapient_apex_qt_helpers.view_builder import build_view
from sapient_apex_server.structures import SapientVersion
from sapient_apex_server.time_util import str_to_datetime

from sapient_apex_replay_gui.core.db_time_range import query_time_range
from sapient_apex_replay_gui.core.replay_config import load_replay_config
from sapient_apex_replay_gui.core.replay_thread import ReplayFinished, ReplayThread

# How much to multiply/divide the speed by for the Faster/Slower buttons
_SPEED_STEP_FACTOR = 2
_SPEED_MIN = 0.05
_SPEED_MAX = 100.0


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.replay_thread = ReplayThread()
        self.replay_thread.log_signal.connect(self.on_log)
        self.replay_thread.state_signal.connect(self.on_replay_finished)

        self.filename_edit = QLineEdit()
        self.open_button = QPushButton("Select File...")

        self.host_edit = QLineEdit("127.0.0.1")
        self.port_spin = QSpinBox()
        self.format_combo = QComboBox()
        self.icd_combo = QComboBox()

        self.start_time_edit = QLineEdit()
        self.end_time_edit = QLineEdit()
        self.use_full_range_button = QPushButton("Use Full File Range")

        self.speed_spin = QDoubleSpinBox()
        self.slower_button = QPushButton("« Slower")
        self.faster_button = QPushButton("Faster »")

        self.start_button = QPushButton("Start Replay")
        self.stop_button = QPushButton("Stop Replay")
        self.status_label = QLabel("Idle")

        self.log_view = QPlainTextEdit()

        self._build_view()
        self._init_field_values()
        self._set_running(False)
        self.startup_open_file()

    def _build_view(self):
        view = {
            "size": QSize(720, 720),
            "windowTitle": "Apex Replay GUI",
            QVBoxLayout(): {
                "contentsMargins": QMargins(6, 6, 6, 6),
                "spacing": 6,
                QHBoxLayout(): {
                    self.filename_edit: {
                        "readOnly": True,
                        "placeholderText": "(No file selected)",
                    },
                    self.open_button: {
                        "maximumWidth": 120,
                        "clicked": self.on_open_clicked,
                    },
                },
                QGroupBox("Connection"): {
                    QFormLayout(): {
                        ("Host:", self.host_edit): {},
                        ("Port:", self.port_spin): {},
                        ("Format:", self.format_combo): {},
                        ("ICD version:", self.icd_combo): {},
                    },
                },
                QGroupBox("Time Range"): {
                    QFormLayout(): {
                        ("Start time:", self.start_time_edit): {},
                        ("End time:", self.end_time_edit): {},
                        ("", self.use_full_range_button): {
                            "clicked": self.on_use_full_range_clicked,
                        },
                    },
                },
                QGroupBox("Speed"): {
                    QHBoxLayout(): {
                        self.slower_button: {"clicked": self.on_slower_clicked},
                        self.speed_spin: {
                            "minimum": _SPEED_MIN,
                            "maximum": _SPEED_MAX,
                            "decimals": 2,
                            "singleStep": 0.25,
                            "value": 1.0,
                            "suffix": "x",
                            "valueChanged": self.on_speed_changed,
                        },
                        self.faster_button: {"clicked": self.on_faster_clicked},
                    },
                },
                QHBoxLayout(): {
                    self.start_button: {"clicked": self.on_start_clicked},
                    self.stop_button: {"clicked": self.on_stop_clicked},
                    self.status_label: {"alignment": Qt.AlignRight | Qt.AlignVCenter},
                },
                self.log_view: {
                    "readOnly": True,
                    "maximumBlockCount": 5000,
                },
            },
        }
        build_view(self, view)

    def _init_field_values(self):
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(5004)
        self.format_combo.addItems(["PROTO", "XML"])
        for version in SapientVersion:
            self.icd_combo.addItem(version.protocol_name, version.name)
        self.icd_combo.setCurrentIndex(self.icd_combo.count() - 1)  # Default to latest
        self._load_connection_defaults()

    def _load_connection_defaults(self):
        """Prefills the connection fields from replay_config.json, if found, instead of leaving
        the hardcoded defaults above. The fields stay editable afterwards either way."""
        config = load_replay_config()
        if "host" in config:
            self.host_edit.setText(config["host"])
        if "port" in config:
            self.port_spin.setValue(config["port"])
        if "format" in config:
            format_index = self.format_combo.findText(config["format"])
            if format_index >= 0:
                self.format_combo.setCurrentIndex(format_index)
        if "icd_version" in config:
            icd_index = self.icd_combo.findText(config["icd_version"])
            if icd_index >= 0:
                self.icd_combo.setCurrentIndex(icd_index)

    def startup_open_file(self):
        if len(sys.argv) > 1:
            self.open_file(sys.argv[1])
            return
        db_paths = sorted(Path("data").glob("*.sqlite"))
        if db_paths:
            self.open_file(str(db_paths[-1]))

    # --- File selection ---------------------------------------------------

    def on_open_clicked(self):
        path = Path().resolve()
        data_path = path.joinpath("data")
        if data_path.exists():
            path = data_path
        result, _ = QFileDialog.getOpenFileName(
            self, "Select Replay Database", str(path), "SQLite databases (*.sqlite)"
        )
        if not result:
            return  # User clicked cancel
        self.open_file(result)

    def open_file(self, filename: str):
        self.filename_edit.setText(filename)
        try:
            start_time, end_time = query_time_range(filename)
            self.start_time_edit.setText(start_time)
            self.end_time_edit.setText(end_time)
            self.status_label.setText("Ready")
        except Exception as e:
            self.status_label.setText(f"Could not read time range: {e}")

    def on_use_full_range_clicked(self):
        filename = self.filename_edit.text()
        if not filename:
            return
        self.open_file(filename)

    # --- Speed control -------------------------------------------------

    def on_speed_changed(self, value: float):
        self.replay_thread.set_speed(value)

    def on_slower_clicked(self):
        self.speed_spin.setValue(max(_SPEED_MIN, self.speed_spin.value() / _SPEED_STEP_FACTOR))

    def on_faster_clicked(self):
        self.speed_spin.setValue(min(_SPEED_MAX, self.speed_spin.value() * _SPEED_STEP_FACTOR))

    # --- Start / stop -------------------------------------------------

    def on_start_clicked(self):
        filename = self.filename_edit.text()
        if not filename:
            QMessageBox.warning(self, "Apex Replay GUI", "Select a database file first.")
            return
        if not Path(filename).exists():
            QMessageBox.warning(self, "Apex Replay GUI", f"File not found: {filename}")
            return
        for label, edit in (
            ("start", self.start_time_edit),
            ("end", self.end_time_edit),
        ):
            try:
                str_to_datetime(edit.text())
            except ValueError:
                QMessageBox.warning(
                    self, "Apex Replay GUI", f"Invalid {label} time: {edit.text()!r}"
                )
                return

        config = {
            "log_level": "INFO",
            "filename": filename,
            "is_outbound": True,
            "host": self.host_edit.text(),
            "port": self.port_spin.value(),
            "start_time": self.start_time_edit.text(),
            "end_time": self.end_time_edit.text(),
            "speed_multiplier": self.speed_spin.value(),
            "format": self.format_combo.currentText(),
            "icd_version": self.icd_combo.currentData(),
        }
        self.log_view.clear()
        self._set_running(True)
        self.status_label.setText("Running")
        self.replay_thread.start(config)

    def on_stop_clicked(self):
        self.status_label.setText("Stopping...")
        self.stop_button.setEnabled(False)
        self.replay_thread.stop()

    def on_replay_finished(self, finished: ReplayFinished):
        self._set_running(False)
        self.status_label.setText(f"Error: {finished.error_str}" if finished.error_str else "Idle")

    def _set_running(self, running: bool):
        self.start_button.setEnabled(not running)
        self.stop_button.setEnabled(running)
        for widget in (
            self.open_button,
            self.host_edit,
            self.port_spin,
            self.format_combo,
            self.icd_combo,
            self.start_time_edit,
            self.end_time_edit,
            self.use_full_range_button,
        ):
            widget.setEnabled(not running)

    # --- Logging -------------------------------------------------

    def on_log(self, message: str):
        self.log_view.appendPlainText(message)

    def closeEvent(self, event):
        self.replay_thread.stop()
        event.accept()
