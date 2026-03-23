# Dynamic Pathing, Asset Management, and COA Plans for Multidisciplinary United States Air Force Operations

## Project Description

A simulation-based research project focused on autonomous and operator-assisted multi-agent path planning in dynamic environments. Initial mission scenarios include search and rescue and disaster response.

## Technologies Used

- **Python** — primary programming language
- **Pygame** — grid-based simulation rendering and interaction
- **Pytest** — unit testing (A* algorithm coverage)
- **Visual Studio Code** — IDE

## Project Structure

```
├── Main.py                  # Standalone waypoint-following demo (pygame)
├── grid_sim/
│   ├── game.py              # Main simulation loop and phase management
│   ├── grid.py              # Grid state, entity placement, wall/fire generation and spread
│   ├── entities.py          # Entity classes: Entity, Wall, Movable; health and fire damage logic
│   ├── metrics.py           # Fuel model, speed tiers, zone tracking, path cost
│   ├── stats.py             # Per-entity stat tracking and summary screen
│   └── config.py            # Grid dimensions, colors, FPS
└── test_astar_combined.py   # A* unit tests
```

## Current Features

**Simulation Phases**

The sim runs in three phases: Planning, Movement, and Finished.

- **Planning** — select entities by clicking, lay out paths with arrow keys, undo steps with Backspace, or clear with C
- **Movement** — entities execute planned paths step by step with live fuel and health tracking
- **Finished** — summary screen shows per-entity stats including steps, efficiency, fuel burned, fire damage taken, and zone completion

**Entity Metrics**

Each entity has randomized attributes assigned at spawn:
- Speed tier (slow / medium / fast) — controls fuel burn rate per step
- Fuel tank — limits total movement distance
- Proximity radius — detection range for nearby entities (visualized as a translucent circle during movement)
- Health — entities take damage from fire and are destroyed if health reaches zero

**Fire and Damage**

- Fire is tracked as a tile set on the grid and spreads outward each tick during movement
- Entities standing on a fire tile take direct damage; entities adjacent to fire take reduced damage
- Damage scales with consecutive ticks of exposure (up to 2x multiplier)
- Destroyed entities stop moving and are marked as incomplete in the summary

**Environment**

- Randomly generated walls and fire clusters on each run
- Start and destination zones are rendered as colored regions with labels

**Controls**

| Key | Action |
|-----|--------|
| Click | Select an entity |
| Arrow keys | Add a step to the selected entity's plan |
| Backspace | Undo last planned step |
| C | Clear selected entity's plan |
| Enter | Start simulation (from Planning or Finished) |
| Space | Pause / resume |
| R | Reset everything |
| ESC | Quit (Main.py only) |

## Dependencies

- Python 3.3+
- [Pygame](https://www.pygame.org/) — `pip install pygame`
- [Pytest](https://pytest.org/) — `pip install pytest`

## Setup

```bash
# Clone the repository
git clone https://github.com/Capstone-Group-O/Capstone.git
cd Capstone

# Install dependencies
pip install pygame pytest
```

## Running the Simulation

```bash
# Grid simulation
python -m grid_sim

# Standalone waypoint demo
python Main.py
```

## Running Tests

```bash
pytest test_astar_combined.py
```

Tests cover: straight-line pathfinding, obstacle avoidance, unreachable goal handling, and dynamic replanning when new obstacles are introduced mid-run.

## Long-Term Goals

1. Integrate autonomous A* path planning into the grid simulation
2. Develop collaborative multi-agent strategies
3. Expand mission scenarios (search and rescue, disaster response)
4. Add dynamic terrain modifiers (weather, fire zones) to the movement cost model
