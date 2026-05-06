from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from .entities import Movable, Wall
from .grid import Grid
from .map_data import MapData
from .metrics import Zone
from .terrain import Barrier, Forest, Water


@dataclass
class RuntimeWorld:
    grid: Grid
    movables: List[Movable]
    start_zone: Zone
    dest_zone: Zone
    objective_cells: List[Tuple[int, int]]
    initial_fire_positions: List[Tuple[int, int]]


TERRAIN_FIELDS = (
    ("walls", Wall),
    ("water", Water),
    ("forest", Forest),
    ("barriers", Barrier),
)


def build_runtime_world(map_data: MapData) -> RuntimeWorld:
    grid = Grid()

    start_zone_data = map_data.start_zone
    dest_zone_data = map_data.dest_zone
    if start_zone_data is None or dest_zone_data is None:
        raise ValueError("Map must include both a start zone and a destination zone.")

    start_zone = Zone(
        start_zone_data.name,
        start_zone_data.x,
        start_zone_data.y,
        start_zone_data.width,
        start_zone_data.height,
        start_zone_data.color,
    )
    dest_zone = Zone(
        dest_zone_data.name,
        dest_zone_data.x,
        dest_zone_data.y,
        dest_zone_data.width,
        dest_zone_data.height,
        dest_zone_data.color,
    )

    for field_name, entity_cls in TERRAIN_FIELDS:
        for x, y in getattr(map_data, field_name):
            if (x, y) not in grid.entities:
                grid.add_entity(entity_cls(x, y))

    movables: List[Movable] = []
    for movable_data in map_data.movables:
        grid.entities.pop((movable_data.x, movable_data.y), None)
        movable = Movable(movable_data.color, movable_data.x, movable_data.y)
        movables.append(movable)
        grid.add_entity(movable)

    objective_cells = list(map_data.objective_cells)
    for cell in objective_cells:
        grid.entities.pop(cell, None)

    grid.objective_cells = set(dest_zone.all_cells())

    fire_positions: List[Tuple[int, int]] = []
    for x, y in map_data.fire:
        if (x, y) in grid.objective_cells:
            continue
        fire_positions.append((x, y))
        grid.add_fire(x, y)

    return RuntimeWorld(
        grid=grid,
        movables=movables,
        start_zone=start_zone,
        dest_zone=dest_zone,
        objective_cells=objective_cells,
        initial_fire_positions=fire_positions,
    )
