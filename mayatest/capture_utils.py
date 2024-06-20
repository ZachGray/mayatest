"""
Utilities for saving and loading view presets from capture module

Example:
save_view_preset(os.path.join(PRESET_PATH, "touch_preset.json"), 'modelPanel4')
preset = load_preset(os.path.join(PRESET_PATH, PRESET_FILE))

"""

import json
from mayatest import capture


def save_preset(path, preset):
    """Save options to path"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(preset, f, indent=4)


def load_preset(path):
    """Load options json from path"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_view_preset(path, view_name):
    """Save view options to path"""
    options = capture.parse_view(view_name)
    save_preset(path, options)


def apply_view_preset(path, view_name):
    """Apply view options from path"""
    preset = load_preset(path)
    capture.apply_view(view_name, **preset)
