# __main__.py
from .game import game
from .launcher import launch
from .map_editor import run_map_editor
from .simulation import SimulationManager


def main():
    next_action = {"action": "launcher"}
    editor_map = None

    while True:
        action = next_action.get("action")

        if action == "launcher":
            next_action = launch(editor_map)
            continue

        if action == "simulation":
            simulation = next_action.get("simulation")
            if simulation is None:
                simulation = SimulationManager()
            return_action = next_action.get("return_action", "launcher")
            if next_action.get("map_data") is not None:
                simulation.editor_map_data = next_action.get("map_data")
            next_action = game(simulation, return_action=return_action)
            continue

        if action == "editor":
            if next_action.get("map_data") is not None:
                editor_map = next_action.get("map_data")
            editor_result = run_map_editor(editor_map)
            if editor_result.map_data is not None:
                editor_map = editor_result.map_data
            if editor_result.action == "test" and editor_result.map_data is not None:
                simulation = SimulationManager(editor_result.map_data)
                simulation.editor_map_data = editor_result.map_data
                next_action = {
                    "action": "simulation",
                    "simulation": simulation,
                    "return_action": "editor",
                    "map_data": editor_result.map_data,
                }
            else:
                next_action = {"action": "launcher"}
            continue

        if action == "quit":
            break

        break


if __name__ == "__main__":
    main()