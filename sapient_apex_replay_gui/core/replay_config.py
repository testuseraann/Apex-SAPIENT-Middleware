#
# Copyright (c) 2019-2024 Roke Manor Research Ltd
#

"""Loads replay_config.json, the same config file sapient_apex_replay.replay's command-line entry
point reads (see get_config() in that module), so the GUI can prefill its connection fields (host,
port, format, ICD version, ...) with it instead of starting from hardcoded defaults every time. The
user can still edit every field afterwards."""

import json
from pathlib import Path


def find_replay_config_path() -> Path | None:
    """Looks for replay_config.json in the current directory, then the parent directory, mirroring
    the search done by sapient_apex_replay.replay.get_config() in case this is run from a nested
    working directory (e.g. by double-clicking replay_gui.exe)."""
    for candidate in (Path("replay_config.json"), Path("..", "replay_config.json")):
        if candidate.exists():
            return candidate
    return None


def load_replay_config() -> dict:
    """Returns the parsed contents of replay_config.json, or {} if the file cannot be found or
    fails to parse."""
    config_path = find_replay_config_path()
    if config_path is None:
        return {}
    try:
        with config_path.open("rb") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
