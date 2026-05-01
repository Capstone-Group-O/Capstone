# map_storage.py
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from .map_data import MapData, blank_map

MISSIONS_DIR = Path(__file__).resolve().parent / "missions"


def ensure_missions_dir() -> Path:
    MISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    return MISSIONS_DIR


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
    return slug or "mission"


def _mission_path_from_title(title: str) -> Path:
    base = _slugify(title)
    candidate = MISSIONS_DIR / f"{base}.json"
    counter = 2
    while candidate.exists():
        candidate = MISSIONS_DIR / f"{base}_{counter}.json"
        counter += 1
    return candidate


def load_or_create_default_map() -> MapData:
    ensure_missions_dir()
    return blank_map()


def save_custom_mission(map_data: MapData, title: str, description: str) -> Path:
    ensure_missions_dir()

    trimmed_title = title.strip() or "Untitled Mission"
    trimmed_description = " ".join(description.strip().split())
    words = trimmed_description.split()
    if len(words) > 50:
        trimmed_description = " ".join(words[:50])

    payload = map_data.to_dict()
    payload["name"] = trimmed_title
    payload["metadata"] = dict(payload.get("metadata", {}))
    payload["metadata"]["title"] = trimmed_title
    payload["metadata"]["description"] = trimmed_description

    target = _mission_path_from_title(trimmed_title)
    with target.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    return target


def list_custom_missions() -> List[Dict[str, object]]:
    ensure_missions_dir()
    missions: List[Dict[str, object]] = []

    for path in sorted(MISSIONS_DIR.glob("*.json")):
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            continue

        metadata = dict(data.get("metadata", {}))
        title = metadata.get("title") or data.get("name") or path.stem
        description = metadata.get("description") or "No description provided."

        missions.append(
            {
                "title": title,
                "description": description,
                "path": path,
            }
        )

    return missions


def load_custom_mission(path: Path) -> MapData:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return MapData.from_dict(data)