from grid_sim.launcher import launch
from grid_sim.game import game

simulation = launch()
if simulation is not None:
    game(simulation)
