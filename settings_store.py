import json
import sys
from pathlib import Path
from typing import Literal

OutputFormat = Literal["wav", "mp3"]

DEFAULT_SETTINGS = {
    "save_dir": "",
    "output_format": "wav",
}


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


def settings_path() -> Path:
    return app_dir() / "settings.json"


def default_save_dir() -> Path:
    return Path.home() / "Music" / "Wavish"


def load_settings() -> dict:
    path = settings_path()
    if not path.exists():
        data = DEFAULT_SETTINGS.copy()
        data["save_dir"] = str(default_save_dir())
        return data
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        data = DEFAULT_SETTINGS.copy()
    if not data.get("save_dir"):
        data["save_dir"] = str(default_save_dir())
    if data.get("output_format") not in ("wav", "mp3"):
        data["output_format"] = "wav"
    return data


def save_settings(save_dir: str, output_format: OutputFormat) -> None:
    path = settings_path()
    path.write_text(
        json.dumps(
            {"save_dir": save_dir, "output_format": output_format},
            indent=2,
        ),
        encoding="utf-8",
    )
