from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from .map_data import MapData, blank_map


MAPS_DIR = Path(__file__).resolve().parent / "maps"
DEFAULT_MAP_PATH = MAPS_DIR / "custom_map.json"


def ensure_maps_dir() -> Path:
    MAPS_DIR.mkdir(parents=True, exist_ok=True)
    return MAPS_DIR


def save_map_data(map_data: MapData, path: Optional[Path] = None) -> Path:
    ensure_maps_dir()
    target = path or DEFAULT_MAP_PATH
    with target.open("w", encoding="utf-8") as fh:
        json.dump(map_data.to_dict(), fh, indent=2)
    return target


def load_map_data(path: Optional[Path] = None) -> MapData:
    target = path or DEFAULT_MAP_PATH
    with target.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return MapData.from_dict(data)


def list_saved_maps() -> List[Path]:
    ensure_maps_dir()
    return sorted(MAPS_DIR.glob("*.json"))


def load_or_create_default_map() -> MapData:
    ensure_maps_dir()
    if DEFAULT_MAP_PATH.exists():
        return load_map_data(DEFAULT_MAP_PATH)
    map_data = blank_map()
    save_map_data(map_data, DEFAULT_MAP_PATH)
    return map_data
