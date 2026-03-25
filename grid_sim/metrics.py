"""
grid_sim/metrics.py

Movement cost model and simulation metrics for SWORD.

Core concepts:
    - Each entity has a fuel tank and a speed setting
    - Higher speed = more fuel burned per step
    - Movement cost is normalized so different entity types can be compared
    - Entities have a proximity diameter for detection/awareness
    - Start and destination are defined as zones (rectangular areas) not just points
"""

import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Optional


# ──────────────────────────────────────────────
# SPEED TIERS — defines the fuel/speed tradeoff
# ──────────────────────────────────────────────

@dataclass
class SpeedTier:
    name: str
    cells_per_tick: int      # how many cells the entity moves per game tick
    fuel_per_step: float     # fuel burned per cell moved

# Slower = cheaper, faster = expensive
SPEED_TIERS = {
    "slow":   SpeedTier("slow",   1, 1.0),
    "medium": SpeedTier("medium", 1, 2.0),   # same cells/tick but burns more (represents effort)
    "fast":   SpeedTier("fast",   2, 3.5),   # 2 cells per tick, heavy fuel cost
}


# ──────────────────────────────────────────────
# ZONE — rectangular area for start/destination
# ──────────────────────────────────────────────

@dataclass
class Zone:
    """A rectangular region on the grid."""
    name: str
    x: int          # top-left corner
    y: int
    width: int
    height: int
    color: Tuple[int, int, int] = (60, 60, 80)

    def contains(self, cx: int, cy: int) -> bool:
        return self.x <= cx < self.x + self.width and self.y <= cy < self.y + self.height

    def random_point(self) -> Tuple[int, int]:
        """Pick a random cell inside this zone."""
        rx = random.randint(self.x, self.x + self.width - 1)
        ry = random.randint(self.y, self.y + self.height - 1)
        return (rx, ry)

    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    def all_cells(self) -> List[Tuple[int, int]]:
        cells = []
        for cx in range(self.x, self.x + self.width):
            for cy in range(self.y, self.y + self.height):
                cells.append((cx, cy))
        return cells


# ──────────────────────────────────────────────
# ENTITY METRICS — attached to each Movable
# ──────────────────────────────────────────────

@dataclass
class EntityMetrics:
    """Tracks fuel, speed, movement cost, and proximity for one entity."""

    # Config (set at creation or randomized)
    max_fuel: float = 100.0
    fuel: float = 100.0
    speed_tier: str = "medium"
    proximity_radius: int = 3          # detection radius in cells

    # Accumulated during sim
    total_fuel_burned: float = 0.0
    total_steps: int = 0
    total_movement_cost: float = 0.0   # normalized cost accumulator
    detected_entities: List = field(default_factory=list)

    # Destination zone tracking
    destination_zone: Optional[Zone] = None
    objective_cell: Optional[Tuple[int, int]] = None
    reached_destination: bool = False

    @property
    def fuel_pct(self) -> float:
        if self.max_fuel <= 0:
            return 0.0
        return (self.fuel / self.max_fuel) * 100.0

    @property
    def is_out_of_fuel(self) -> bool:
        return self.fuel <= 0

    def get_speed_tier(self) -> SpeedTier:
        return SPEED_TIERS.get(self.speed_tier, SPEED_TIERS["medium"])

    def burn_fuel_for_step(self) -> bool:
        """
        Burns fuel for one step at the current speed tier.
        Returns False if not enough fuel remaining.
        """
        tier = self.get_speed_tier()
        cost = tier.fuel_per_step

        if self.fuel < cost:
            return False

        self.fuel -= cost
        self.total_fuel_burned += cost
        self.total_steps += 1

        # Normalized movement cost: fuel_per_step / cells_per_tick
        # This lets us compare entities at different speeds on the same scale
        normalized = cost / max(tier.cells_per_tick, 1)
        self.total_movement_cost += normalized

        return True

    def check_proximity(self, self_x, self_y, other_x, other_y) -> bool:
        """Returns True if (other_x, other_y) is within proximity diameter."""
        dist = math.sqrt((other_x - self_x) ** 2 + (other_y - self_y) ** 2)
        return dist <= self.proximity_radius

    def check_in_zone(self, x, y) -> bool:
        """
        Check if entity has reached its assigned objective.

        If an objective cell is assigned, the entity must reach that specific
        cell. Otherwise, falling back to the destination zone preserves the
        original zone-based behavior.
        """
        if self.objective_cell is not None:
            if (x, y) == self.objective_cell:
                self.reached_destination = True
                return True
            return False

        if self.destination_zone is None:
            return False
        if self.destination_zone.contains(x, y):
            self.reached_destination = True
            return True
        return False


# ──────────────────────────────────────────────
# RANDOMIZED METRIC GENERATION
# ──────────────────────────────────────────────

def random_entity_metrics(
    fuel_range: Tuple[float, float] = (60.0, 120.0),
    proximity_range: Tuple[int, int] = (2, 5),
    speed_tier: Optional[str] = None,
) -> EntityMetrics:
    """
    Generate randomized metrics for an entity.
    If speed_tier is None, picks one at random.
    """
    fuel = round(random.uniform(*fuel_range), 1)
    prox = random.randint(*proximity_range)

    if speed_tier is None:
        speed_tier = random.choice(list(SPEED_TIERS.keys()))

    return EntityMetrics(
        max_fuel=fuel,
        fuel=fuel,
        speed_tier=speed_tier,
        proximity_radius=prox,
    )


# ──────────────────────────────────────────────
# DYNAMIC PATH COST
# ──────────────────────────────────────────────

def cell_movement_cost(metrics: EntityMetrics, terrain_modifier: float = 1.0) -> float:
    """
    Calculate the cost of moving into a cell.
    Combines the entity's speed tier fuel cost with an optional terrain modifier.

    terrain_modifier: 1.0 = normal, 2.0 = rough terrain (double cost), etc.
    This is where you plug in dynamic costs later (weather, fire zones, etc).
    """
    tier = metrics.get_speed_tier()
    return tier.fuel_per_step * terrain_modifier


def path_total_cost(metrics: EntityMetrics, path_length: int, terrain_modifier: float = 1.0) -> float:
    """Estimate total fuel cost for a planned path before committing."""
    per_cell = cell_movement_cost(metrics, terrain_modifier)
    return per_cell * path_length


def can_complete_path(metrics: EntityMetrics, path_length: int, terrain_modifier: float = 1.0) -> bool:
    """Check if an entity has enough fuel to complete a planned path."""
    cost = path_total_cost(metrics, path_length, terrain_modifier)
    return metrics.fuel >= cost
