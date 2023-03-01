from time import sleep

from asciimatics.effects import Print
from asciimatics.renderers import Box
from asciimatics.scene import Scene
from asciimatics.screen import ManagedScreen

from blueye.sdk import Drone


def print_state(screen: ManagedScreen, drone: Drone):
    """Updates and prints some of the information from the drone"""
    screen.print_at(f"Lights: {drone.lights * 100} %", 2, 1)

    screen.print_at(f"Auto-depth: {'On' if drone.motion.auto_depth_active else 'Off':>5}", 2, 3)
    screen.print_at(f"Auto-heading: {'On' if drone.motion.auto_heading_active else 'Off':>3}", 2, 4)

    screen.print_at(f"Depth: {drone.depth} mm", 2, 6)

    screen.print_at(f"Roll: {drone.pose['roll']:7.2f}°", 2, 8)
    screen.print_at(f"Pitch: {drone.pose['pitch']:6.2f}°", 2, 9)
    screen.print_at(f"Yaw: {drone.pose['yaw']:8.2f}°", 2, 10)


def state_printer(drone: Drone):
    """Draws a box and fills it with information from the drone"""
    with ManagedScreen() as screen:
        effects = [Print(screen, Box(screen.width, 12, uni=screen.unicode_aware), 0, 0)]
        screen.set_scenes([Scene(effects)])
        while True:
            screen.draw_next_frame()
            print_state(screen, drone)
            screen.refresh()
            sleep(0.2)


if __name__ == "__main__":
    myDrone = Drone()
    state_printer(myDrone)
