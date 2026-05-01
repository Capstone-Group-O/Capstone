# map_storage.py
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List

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


def save_custom_mission(
    map_data: MapData,
    title: str,
    description: str,
    existing_path: Path | None = None,
) -> Path:
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

    current_path = existing_path
    if current_path is None:
        current_meta_path = payload["metadata"].get("mission_path")
        if current_meta_path:
            current_path = Path(current_meta_path)

    # Key behavior:
    # - existing mission => overwrite same file
    # - new mission => create a new file
    if current_path is not None:
        target = Path(current_path)
    else:
        target = _mission_path_from_title(trimmed_title)

    payload["metadata"]["mission_path"] = str(target)

    with target.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)

    map_data.metadata["title"] = trimmed_title
    map_data.metadata["description"] = trimmed_description
    map_data.metadata["mission_path"] = str(target)
    map_data.name = trimmed_title
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
    mission = MapData.from_dict(data)
    mission.metadata["mission_path"] = str(path)
    return mission


def delete_custom_mission(path: Path) -> bool:
    try:
        Path(path).unlink()
        return True
    except FileNotFoundError:
        return False