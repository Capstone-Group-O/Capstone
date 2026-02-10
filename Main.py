import math
import sys
import pygame


# Config stuff
WIDTH = 1000
HEIGHT = 600
FPS = 60

BG_COLOR = (20, 20, 28)
PATH_COLOR = (120, 120, 160)
WAYPOINT_COLOR = (180, 180, 220)
ENDPOINT_COLOR = (90, 220, 140)

ENTITY_COLOR = (240, 120, 120)
TARGET_COLOR = (255, 220, 120)

ENTITY_RADIUS = 14
ENTITY_SPEED_PX_PER_SEC = 220.0  # Movement speed


# Helper functions
def vec2(x, y) -> pygame.Vector2:
    return pygame.Vector2(float(x), float(y))


def move_toward(current: pygame.Vector2, target: pygame.Vector2, max_step: float) -> pygame.Vector2:
    """
    Move current toward target by at most max_step (in pixels).
    Returns the new position.
    """
    # Moves current toward target by at most max_step (in pixels) and returns the new position
    to_target = target - current
    dist = to_target.length()

    if dist <= max_step or dist == 0:
        return target

    return current + to_target.normalize() * max_step


# Main block, this will be split into different classes soon
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("GAME OF THE YEAR 2027")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    # List of waypoints and an end point. Path is fixed
    path = [
        vec2(120, 450),
        vec2(200, 180),
        vec2(420, 160),
        vec2(650, 260),
        vec2(820, 120),
        vec2(880, 420),  # end point
    ]

    start_pos = path[0]
    end_pos = path[-1]

    entity_pos = start_pos.copy()
    waypoint_index = 1  # Next target

    paused = False
    finished = False

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # Seconds since last frame

        # Main events (will almost 100% get outsourced from this file)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Main user "functions"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    # Reset
                    entity_pos = start_pos.copy()
                    waypoint_index = 1
                    paused = False
                    finished = False

        # Update
        if not paused and not finished:
            target = path[waypoint_index]
            step = ENTITY_SPEED_PX_PER_SEC * dt
            entity_pos = move_toward(entity_pos, target, step)

            # Go to next waypoint if we've reached the target or stop at the end
            if entity_pos == target:
                if waypoint_index < len(path) - 1:
                    waypoint_index += 1
                else:
                    finished = True

        # Rendering BS
        screen.fill(BG_COLOR)

        # Drawing path lines
        pygame.draw.lines(screen, PATH_COLOR, False, [(p.x, p.y) for p in path], 4)

        # Drawing waypoints
        # i is the index here and p is the object itself
        for i, p in enumerate(path):
            if i == len(path) - 1:
                pygame.draw.circle(screen, ENDPOINT_COLOR, (int(p.x), int(p.y)), 10)
            else:
                pygame.draw.circle(screen, WAYPOINT_COLOR, (int(p.x), int(p.y)), 8)

        # Drawing current target waypoint (if not finished)
        if not finished:
            t = path[waypoint_index]
            pygame.draw.circle(screen, TARGET_COLOR, (int(t.x), int(t.y)), 14, 2)

        # Drawing super basic entity
        pygame.draw.circle(screen, ENTITY_COLOR, (int(entity_pos.x), int(entity_pos.y)), ENTITY_RADIUS)

        # HUD text (completely unnecessary but fun anyways)
        status = "PAUSED" if paused else ("FINISHED" if finished else "RUNNING")
        hud_lines = [
            f"Status: {status}",
            f"Waypoint: {waypoint_index}/{len(path)-1}   (End: {int(end_pos.x)}, {int(end_pos.y)})",
            "Controls: SPACE = pause/resume, R = reset, ESC = quit",
        ]
        y = 10
        for line in hud_lines:
            surf = font.render(line, True, (230, 230, 240))
            screen.blit(surf, (10, y))
            y += 22

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
