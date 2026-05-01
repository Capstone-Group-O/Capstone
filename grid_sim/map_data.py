from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional, Tuple

from .config import GRID_HEIGHT, GRID_WIDTH


Cell = Tuple[int, int]
Color = Tuple[int, int, int]


@dataclass
class ZoneData:
    name: str
    x: int
    y: int
    width: int
    height: int
    color: Color = (60, 60, 80)


@dataclass
class MovableSpawnData:
    x: int
    y: int
    color: Color = (0, 0, 255)


@dataclass
class MapData:
    name: str = "custom_map"
    width: int = GRID_WIDTH
    height: int = GRID_HEIGHT
    walls: List[Cell] = field(default_factory=list)
    water: List[Cell] = field(default_factory=list)
    forest: List[Cell] = field(default_factory=list)
    barriers: List[Cell] = field(default_factory=list)
    fire: List[Cell] = field(default_factory=list)
    movables: List[MovableSpawnData] = field(default_factory=list)
    start_zone: Optional[ZoneData] = None
    dest_zone: Optional[ZoneData] = None
    objective_cells: List[Cell] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MapData":
        movables = [MovableSpawnData(**item) for item in data.get("movables", [])]
        start_zone = ZoneData(**data["start_zone"]) if data.get("start_zone") else None
        dest_zone = ZoneData(**data["dest_zone"]) if data.get("dest_zone") else None
        return cls(
            name=data.get("name", "custom_map"),
            width=data.get("width", GRID_WIDTH),
            height=data.get("height", GRID_HEIGHT),
            walls=[tuple(cell) for cell in data.get("walls", [])],
            water=[tuple(cell) for cell in data.get("water", [])],
            forest=[tuple(cell) for cell in data.get("forest", [])],
            barriers=[tuple(cell) for cell in data.get("barriers", [])],
            fire=[tuple(cell) for cell in data.get("fire", [])],
            movables=movables,
            start_zone=start_zone,
            dest_zone=dest_zone,
            objective_cells=[tuple(cell) for cell in data.get("objective_cells", [])],
            metadata=dict(data.get("metadata", {})),
        )


def blank_map(name: str = "custom_map") -> MapData:
    return MapData(
        name=name,
        start_zone=ZoneData("Start", 1, 1, 4, 4, (40, 80, 120)),
        dest_zone=ZoneData("Objective", 24, 24, 4, 4, (80, 120, 40)),
        movables=[MovableSpawnData(2, 2), MovableSpawnData(3, 2)],
        objective_cells=[(25, 25), (26, 26)],
    )
