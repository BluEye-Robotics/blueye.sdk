from time import sleep

from asciimatics.effects import Print
from asciimatics.renderers import Box
from asciimatics.scene import Scene
from asciimatics.screen import ManagedScreen

from blueye.sdk import Pioneer


def print_state(screen: ManagedScreen, pioneer: Pioneer):
    """Updates and prints some of the information from the drone"""
    screen.print_at(f"Lights: {pioneer.lights * 100 // 255:3d} %", 2, 1)

    screen.print_at(
        f"Auto-depth: {'On' if pioneer.motion.auto_depth_active else 'Off':>5}", 2, 3
    )
    screen.print_at(
        f"Auto-heading: {'On' if pioneer.motion.auto_heading_active else 'Off':>3}",
        2,
        4,
    )

    screen.print_at(f"Depth: {pioneer.depth} mm", 2, 6)

    screen.print_at(f"Roll: {pioneer.pose['roll']:7.2f}°", 2, 8)
    screen.print_at(f"Pitch: {pioneer.pose['pitch']:6.2f}°", 2, 9)
    screen.print_at(f"Yaw: {pioneer.pose['yaw']:8.2f}°", 2, 10)


def state_printer(pioneer: Pioneer):
    """Draws a box and fills it with information from the drone"""
    with ManagedScreen() as screen:
        effects = [Print(screen, Box(screen.width, 12, uni=screen.unicode_aware), 0, 0)]
        screen.set_scenes([Scene(effects)])
        while True:
            screen.draw_next_frame()
            print_state(screen, pioneer)
            screen.refresh()
            sleep(0.2)


if __name__ == "__main__":
    p = Pioneer(slaveModeEnabled=True)
    state_printer(p)
