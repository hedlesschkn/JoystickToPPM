import pygame #(pip install pygame)
import time
from abc import ABC, abstractmethod

pygame.init()

# This is a simple class that will help us print to the screen.
# It has nothing to do with the joysticks, just outputting the
# information.
class TextPrint:
    def __init__(self):
        self.reset()
        self.font = pygame.font.Font(None, 25)

    def tprint(self, screen, text):
        text_bitmap = self.font.render(text, True, (0, 0, 0))
        screen.blit(text_bitmap, (self.x, self.y))
        self.y += self.line_height

    def reset(self):
        self.x = 10
        self.y = 10
        self.line_height = 15

    def indent(self):
        self.x += 10

    def unindent(self):
        self.x -= 10

# define a simulated-gimbal abstract class (interface) and individual joystick classes
# these will take joystick information in and output simulated gimbal results
# F/B(elevator), L/R(Aileron), and Weapon(Throttle) will be simulated
class SimGimbal(ABC):
    def __init__(self, joystick: pygame.joystick.Joystick):
        self.joystick = joystick
    @abstractmethod
    def get_throttle(self) -> float:
        return 0
    @abstractmethod
    def get_ail(self) -> float:
        return 0
    @abstractmethod
    def get_elev(self) -> float:
        return 0

#concrete subclasses of SimGimbal
class DDRPad_Gimbal(SimGimbal): #TODO
    def get_throttle(self) -> float:
        return (9)
    def get_ail(self) -> float:
        return (self.joystick.get_button(0) - 0.1)
    def get_elev(self) -> float:
        return (self.joystick.get_button(0) - 0.1)

class Drum_Gimbal(SimGimbal): #TODO
    def get_throttle(self) -> float:
        return (8)
    def get_ail(self) -> float:
        return (self.joystick.get_button(0) + 0.1)
    def get_elev(self) -> float:
        return (self.joystick.get_button(0) + 0.1)

class SteeringWheel_Gimbal(SimGimbal): #TODO
    def get_throttle(self) -> float:
        return (7)
    def get_ail(self) -> float:
        return (self.joystick.get_button(0) + 0.1)
    def get_elev(self) -> float:
        return (self.joystick.get_button(0) + 0.1)

#Right Gimbal for drive, Left Trigger for Weapon
class Xbox360_Gimbal(SimGimbal): #working
    def get_throttle(self) -> float:
        return (self.joystick.get_axis(4)) #L trigger
    def get_ail(self) -> float:
        return (self.joystick.get_axis(2)) #R gimbal L/R
    def get_elev(self) -> float:
        return (self.joystick.get_axis(3)*-1) #R gimbal U/D

#Strum for Forwards/Backwards, 
class Guitar_Gimbal(SimGimbal):
    def __init__(self, joystick: pygame.joystick.Joystick):
        super().__init__(joystick)
        self.pressure = 0
        self.max_force = 1.0
        self.growth_rate = 0.05
        self.decay_rate = 0.02

    def green_button(self):
        return self.joystick.get_button(1)
    def red_button(self):
        return self.joystick.get_button(0)
    def yellow_button(self):
        return self.joystick.get_button(3)
    def blue_button(self):
        return self.joystick.get_button(2)
    def orange_button(self):
        return self.joystick.get_button(6)

    def get_throttle(self) -> float:
        return (self.orange_button())
    def get_ail(self):
        self.pressure = update_hold_pressure(self.pressure, self.blue_button(), self.green_button(), self.max_force, self.growth_rate, self.decay_rate)
        return self.pressure
    def get_elev(self) -> float:
        return (self.joystick.get_hat(0)[1]*-1) #strum down = forward, up=backwards

class KeyboardMouse_Gimbal(SimGimbal): #TODO
    def get_throttle(self) -> float:
        return (4)
    def get_ail(self) -> float:
        return (self.joystick.get_button(0) + 0.1)
    def get_elev(self) -> float:
        return (self.joystick.get_button(0) + 0.1)

# Factory function to determine joystick type
def gimbal_factory(joystick: pygame.joystick.Joystick) -> SimGimbal:
    joystick_name = joystick.get_name().lower()
    #print("Factory Name: ", joystick_name)
    if "gamepad" in joystick_name: #USB Gamepad
        return DDRPad_Gimbal(joystick)
    elif "drum" in joystick_name: #Licensed by Sony Computer Entertainment America Harmonix Drum Kit for PlayStation(R)3
        return Drum_Gimbal(joystick)
    elif "windows" in joystick_name: #MY-POWER CO.,LTD Controller For Windows
        return Guitar_Gimbal(joystick)
    elif "steering" in joystick_name:
        return SteeringWheel_Gimbal(joystick)
    elif "xbox" in joystick_name:
        return Xbox360_Gimbal(joystick) #Xbox 360 Controller
    else:
        return KeyboardMouse_Gimbal(joystick)

# Calculates pressure based on holding a button down.
# Positive input increases pressure, negative input decreases it, and it decays over time.
def update_hold_pressure(pressure, positive_input, negative_input, max_force, growth_rate, decay_rate):
    old_pressure = pressure  # Store old pressure for debugging

    if positive_input:
        pressure = min(max_force, pressure + growth_rate)
    elif negative_input:
        pressure = max(-max_force, pressure - growth_rate)
    else:
        if pressure > 0:
            pressure = max(0, pressure - decay_rate)
        elif pressure < 0:
            pressure = min(0, pressure + decay_rate)
    
    print(f"Old Pressure: {old_pressure}, New Pressure: {pressure}, Pos Input: {positive_input}, Neg Input: {negative_input}")
    
    return pressure


# Constants for hit-based pressure
HIT_WINDOW = 1.0  # Seconds to track hits
MAX_HITS = 10     # Maximum hits per second for full pressure

# Tracking hit timestamps
hit_timestamps = []

# Calculates pressure based on how frequently a button is hit.
# The more frequent the hits within a set window, the higher the pressure.
def update_hit_pressure():
    """Calculate pressure based on hit frequency."""
    now = time.time()
    hit_timestamps[:] = [t for t in hit_timestamps if now - t <= HIT_WINDOW]
    return min(1.0, len(hit_timestamps) / MAX_HITS)

def main():
    # Set the width and height of the screen (width, height), and name the window.
    screen = pygame.display.set_mode((500, 700),pygame.RESIZABLE)
    pygame.display.set_caption("Joystick example")

    # Used to manage how fast the screen updates.
    clock = pygame.time.Clock()

    # Get ready to print.
    text_print = TextPrint()

    # This dict can be left as-is, since pygame will generate a
    # pygame.JOYDEVICEADDED event for every joystick connected
    # at the start of the program.
    joysticks = {}

    done = False
    while not done:
        # Event processing step.
        # Possible joystick events: JOYAXISMOTION, JOYBALLMOTION, JOYBUTTONDOWN,
        # JOYBUTTONUP, JOYHATMOTION, JOYDEVICEADDED, JOYDEVICEREMOVED
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True  # Flag that we are done so we exit this loop.

            if event.type == pygame.JOYBUTTONDOWN:
                print("Joystick button pressed.")
                print("Joystick Name: ", joystick.get_name())
                if event.button == 0:
                    joystick = joysticks[event.instance_id]
                    if joystick.rumble(1, 1, 500):
                        print(f"Rumble effect played on joystick {event.instance_id}")

            if event.type == pygame.JOYBUTTONUP:
                print("Joystick button released.")

            # Handle hotplugging
            if event.type == pygame.JOYDEVICEADDED:
                # This event will be generated when the program starts for every
                # joystick, filling up the list without needing to create them manually.
                joy = pygame.joystick.Joystick(event.device_index)
                joysticks[joy.get_instance_id()] = joy
                print(f"Joystick {joy.get_instance_id()} connencted")

            if event.type == pygame.JOYDEVICEREMOVED:
                del joysticks[event.instance_id]
                print(f"Joystick {event.instance_id} disconnected")

        # Drawing step
        # First, clear the screen to white. Don't put other drawing commands
        # above this, or they will be erased with this command.
        screen.fill((255, 255, 255))
        text_print.reset()

        # Get count of joysticks.
        joystick_count = pygame.joystick.get_count()

        text_print.tprint(screen, f"Number of joysticks: {joystick_count}")
        text_print.indent()

        # For each joystick:
        for joystick in joysticks.values():
            jid = joystick.get_instance_id()

            text_print.tprint(screen, f"Joystick {jid}")
            text_print.indent()

            # Get the name from the OS for the controller/joystick.
            name = joystick.get_name()
            text_print.tprint(screen, f"Joystick name: {name}")

            guid = joystick.get_guid()
            text_print.tprint(screen, f"GUID: {guid}")

            power_level = joystick.get_power_level()
            text_print.tprint(screen, f"Joystick's power level: {power_level}")
            if (name != "3Dconnexion KMJ Emulator") and (name != "SpaceNavigator"):
                # Usually axis run in pairs, up/down for one, and left/right for
                # the other. Triggers count as axes.
                axes = joystick.get_numaxes()
                text_print.tprint(screen, f"Number of axes: {axes}")
                text_print.indent()

                for i in range(axes):
                    axis = joystick.get_axis(i)
                    text_print.tprint(screen, f"Axis {i} value: {axis:>6.3f}")
                text_print.unindent()

                buttons = joystick.get_numbuttons()
                text_print.tprint(screen, f"Number of buttons: {buttons}")
                text_print.indent()

                for i in range(buttons):
                    button = joystick.get_button(i)
                    text_print.tprint(screen, f"Button {i:>2} value: {button}")
                text_print.unindent()

                hats = joystick.get_numhats()
                text_print.tprint(screen, f"Number of hats: {hats}")
                text_print.indent()

                # Hat position. All or nothing for direction, not a float like
                # get_axis(). Position is a tuple of int values (x, y).
                for i in range(hats):
                    hat = joystick.get_hat(i)
                    text_print.tprint(screen, f"Hat {i} value: {str(hat)}")
                text_print.unindent()
                text_print.tprint(screen, f"Simulated Gimbals:")
                text_print.indent()
                gimbal = gimbal_factory(joystick) #figure out which controller is being used and create that joystick_gimbal class object

                text_print.tprint(screen, f"Joystick Name: {joystick.get_name()}")
                text_print.tprint(screen, f"F/B(Ele): {gimbal.get_elev():>6.3f}")
                text_print.tprint(screen, f"L/R(Ail): {gimbal.get_ail():>6.3f}")
                text_print.tprint(screen, f"Weapon(T): {gimbal.get_throttle():>6.3f}")
                text_print.unindent()

            text_print.unindent()

        # Go ahead and update the screen with what we've drawn.
        pygame.display.flip()

        # Limit to 30 frames per second.
        clock.tick(30)


if __name__ == "__main__":
    main()
    # If you forget this line, the program will 'hang'
    # on exit if running from IDLE.
    pygame.quit()