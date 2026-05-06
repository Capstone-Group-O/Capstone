"""
grid_sim/sim_export.py

Exports simulation summary data to a timestamped JSON file in sim_results/.
Called automatically when the simulation reaches PHASE_FINISHED.
"""

import json
import os
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .simulation import SimulationManager

_RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sim_results")


def _stop_reason(entity, stats_data: dict) -> dict:
    """
    Determine why an entity stopped and whether it succeeded.

    Returns a dict with:
        code   — machine-readable key
        label  — short human label shown in the UI
        detail — full sentence explanation for the docs
    """
    m = getattr(entity, "metrics", None)

    if entity.destroyed:
        return {
            "code": "destroyed_by_fire",
            "label": "Destroyed by Fire",
            "detail": (
                f"Entity was destroyed before reaching its destination. "
                f"It took {entity.fire_damage_taken:.1f} total fire damage over "
                f"{entity.time_in_fire} tick(s) on fire and "
                f"{entity.time_near_fire} tick(s) adjacent to fire, "
                f"reducing health to zero."
            ),
        }

    if m is not None and m.ran_out_of_fuel:
        steps_remaining = stats_data["steps_planned"] - stats_data["steps_taken"]
        return {
            "code": "out_of_fuel",
            "label": "Out of Fuel",
            "detail": (
                f"Entity exhausted its fuel supply ({m.max_fuel:.1f} units) "
                f"after {stats_data['steps_taken']} step(s) with approximately "
                f"{steps_remaining} planned step(s) still remaining. "
                f"It did not reach its destination."
            ),
        }

    if m is not None and m.reached_destination:
        return {
            "code": "reached_destination",
            "label": "Mission Success",
            "detail": (
                f"Entity successfully completed its planned path and reached "
                f"the destination zone '{m.destination_zone.name if m.destination_zone else 'Objective'}'. "
                f"Fuel remaining: {m.fuel:.1f}/{m.max_fuel:.1f} units. "
                f"Health remaining: {entity.health:.1f}/100."
            ),
        }

    # Path completed but objective cell / zone was not reached
    return {
        "code": "completed_path_missed_destination",
        "label": "Path Complete — Destination Missed",
        "detail": (
            f"Entity completed all {stats_data['steps_planned']} planned step(s) "
            f"but did not arrive at the destination zone. "
            f"The planned path may not have extended far enough, or the entity "
            f"was blocked before the final cell."
        ),
    }


def _entity_summary(index: int, entity, stats_data: dict) -> dict:
    m = getattr(entity, "metrics", None)
    reason = _stop_reason(entity, stats_data)

    nav = {}
    fuel_block = {}
    if m is not None:
        nav = {
            "reached_destination": m.reached_destination,
            "destination_zone": m.destination_zone.name if m.destination_zone else None,
            "objective_cell": list(m.objective_cell) if m.objective_cell else None,
            "proximity_radius": m.proximity_radius,
        }
        fuel_block = {
            "fuel_remaining": round(m.fuel, 2),
            "max_fuel": round(m.max_fuel, 2),
            "fuel_burned": round(m.total_fuel_burned, 2),
            "fuel_pct": round(m.fuel_pct, 1),
            "ran_out_of_fuel": m.ran_out_of_fuel,
            "speed_tier": m.speed_tier,
            "total_movement_cost": round(m.total_movement_cost, 2),
        }

    return {
        "entity_id": index + 1,
        "color": list(entity.color),
        "stop_reason": reason,
        "movement": {
            "steps_planned": stats_data["steps_planned"],
            "steps_taken": stats_data["steps_taken"],
            "blocked_moves": stats_data["collisions"],
            "efficiency": round(stats_data.get("efficiency", 0.0), 4),
            "start_position": list(stats_data["start"]),
            "end_position": list(stats_data.get("end", [entity.x_pos, entity.y_pos])),
            "direct_distance": round(stats_data.get("direct_dist", 0.0), 2),
        },
        "health": {
            "health_remaining": round(entity.health, 2),
            "max_health": entity.max_health,
            "fire_damage_taken": round(entity.fire_damage_taken, 2),
            "time_in_fire_ticks": entity.time_in_fire,
            "time_near_fire_ticks": entity.time_near_fire,
            "destroyed": entity.destroyed,
        },
        "fuel": fuel_block,
        "navigation": nav,
    }


def _overall_outcome(entity_summaries: list) -> dict:
    codes = [e["stop_reason"]["code"] for e in entity_summaries]
    success_count = codes.count("reached_destination")
    total = len(codes)

    if success_count == total:
        outcome = "success"
        detail = "All entities reached their destination."
    elif success_count > 0:
        outcome = "partial"
        detail = f"{success_count} of {total} entities reached the destination."
    else:
        outcome = "failure"
        reasons = set(codes) - {"reached_destination"}
        parts = []
        if "destroyed_by_fire" in reasons:
            parts.append("fire damage")
        if "out_of_fuel" in reasons:
            parts.append("fuel exhaustion")
        if "completed_path_missed_destination" in reasons:
            parts.append("incomplete path planning")
        detail = f"No entities reached the destination. Causes: {', '.join(parts)}."

    return {"outcome": outcome, "detail": detail}


def export_sim_results(sim: "SimulationManager") -> str:
    """
    Build a simulation summary dict and write it to sim_results/<timestamp>.json.
    Returns the path to the written file.
    """
    stats_values = list(sim.stats._data.values())
    entity_summaries = [
        _entity_summary(i, d["entity"], d)
        for i, d in enumerate(stats_values)
    ]

    overall = _overall_outcome(entity_summaries)
    mission_name = sim.source_map_data.name if sim.source_map_data else "unknown"

    payload = {
        "schema_version": "1.0",
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "mission_name": mission_name,
        "outcome": overall["outcome"],
        "outcome_detail": overall["detail"],
        "entity_count": len(entity_summaries),
        "entities": entity_summaries,
    }

    os.makedirs(_RESULTS_DIR, exist_ok=True)
    filename = datetime.now().strftime("sim_%Y%m%d_%H%M%S.json")
    filepath = os.path.join(_RESULTS_DIR, filename)

    with open(filepath, "w") as f:
        json.dump(payload, f, indent=2)

    return filepath
