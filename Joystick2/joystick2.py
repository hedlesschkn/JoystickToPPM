import pygame
import json #to load config
import sys #to load config
print(sys.path)
import platform #to check OS
import time
from abc import ABC, abstractmethod
from config import get_config, get_GPIO #local config

#launch pigpio if Linux & return True, else return False
pigpio = get_GPIO()

# Detect the OS
def get_system():
    os_name = platform.system()
    if os_name == "Windows":
        return "Windows"
    elif os_name == "Linux":
        # Further check if it's a Raspberry Pi
        try:
            with open("/sys/firmware/devicetree/base/model", "r") as f:
                if "Raspberry Pi" in f.read():
                    return "Raspbian"
        except FileNotFoundError:
            pass
    return "Unknown"

# Constants for hit-based pressure
HIT_WINDOW = 1.0  # Seconds to track hits
MAX_HITS = 10     # Maximum hits per second for full pressure
hit_timestamps = []

def remap(num, inMin, inMax, inMid, outMin, outMax, outMid):
    
    # Calculate the input and output ranges
    inRange = inMax - inMin
    outRange = outMax - outMin
    
    # Calculate the input and output midpoints
    inMidRange = inMid - inMin
    outMidRange = outMid - outMin
    
    # Determine the input and output halves
    if num <= inMid:
        # Map the lower half
        remapped_value = outMid - (inMid - num) / inMidRange * outMidRange
    else:
        # Map the upper half
        remapped_value = outMid + (num - inMid) / (inRange - inMidRange) * (outRange - outMidRange)
    
    # Ensure the remapped value is within the output range
    remapped_value = max(outMin, min(remapped_value, outMax))
    
    return remapped_value

def update_hold_pressure(pressure, positive_input, negative_input, max_force, growth_rate, decay_rate):
    if positive_input:
        pressure = min(max_force, pressure + growth_rate)
    elif negative_input:
        pressure = max(-max_force, pressure - growth_rate)
    else:
        if pressure > 0:
            pressure = max(0, pressure - decay_rate)
        elif pressure < 0:
            pressure = min(0, pressure + decay_rate)
    return pressure

def update_hold_pressure_multi(pressure, positive_input, negative_input, max_force, growth_rate, decay_rate, last_pressed_direction):
    if positive_input and negative_input:
        if last_pressed_direction == 'positive':
            pressure = min(max_force, pressure + growth_rate)
        elif last_pressed_direction == 'negative':
            pressure = max(-max_force, pressure - growth_rate)
    elif positive_input:
        pressure = min(max_force, pressure + growth_rate)
        last_pressed_direction = 'negative'
    elif negative_input:
        pressure = max(-max_force, pressure - growth_rate)
        last_pressed_direction = 'positive'
    else:
        if pressure > 0:
            pressure = max(0, pressure - decay_rate)
        elif pressure < 0:
            pressure = min(0, pressure + decay_rate)
        last_pressed_direction = None #reset last pressed direction when nothing is pressed
    return pressure, last_pressed_direction

def update_hit_pressure(pressure, positive_input, negative_input, max_force, growth_rate, decay_rate, hit_timestamps, HIT_WINDOW, MAX_HITS):
    now = time.time()
    hit_timestamps[:] = [t for t in hit_timestamps if now - t <= HIT_WINDOW]

    if positive_input:
        hit_timestamps.append(now)
        pressure = min(max_force, pressure + growth_rate)
    elif negative_input:
        # No timestamps added here for negative input.
        pressure = max(-max_force, pressure - growth_rate)
    else:
        if pressure > 0:
            pressure = max(0, pressure - decay_rate)
        elif pressure < 0:
            pressure = min(0, pressure + decay_rate)

    hit_density = min(1.0, len(hit_timestamps) / MAX_HITS)
    if pressure > 0:
        pressure = min(pressure, hit_density * max_force)
    elif pressure < 0:
        # Negative pressure is not affected by hit density.
        pass

    return pressure

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
class DDRPad_Gimbal(SimGimbal): #working
    def __init__(self, joystick: pygame.joystick.Joystick):
        super().__init__(joystick)
        self.config = get_config()["DDRPad_Gimbal"]

        self.throttle = -1 # set throttle to "off"
        self.ail_pressure = 0
        self.ail_max_force = 1.0
        self.ail_growth_rate = 0.1
        self.ail_decay_rate = 0.05
        self.elev_pressure = 0
        self.elev_max_force = 1.0
        self.elev_growth_rate = 0.1
        self.elev_decay_rate = 0.05
        self.ail_last_pressed = None
        self.elev_last_pressed = None

    def up_button(self):
        return self.joystick.get_button(self.config["up"])
    def down_button(self):
        return self.joystick.get_button(self.config["down"])
    def left_button(self):
        return self.joystick.get_button(self.config["left"])
    def right_button(self):
        return self.joystick.get_button(self.config["right"])
    def X_button(self):
        return self.joystick.get_button(self.config["X"])
    def O_button(self):
        return self.joystick.get_button(self.config["O"])
    def back_button(self):
        return self.joystick.get_button(self.config["back"])
    def select_button(self):
        return self.joystick.get_button(self.config["select"])

    def get_throttle(self) -> float:
        if self.back_button():
            self.throttle = -1 # set throttle to "off"
        elif self.select_button():
            self.throttle = -1 # set throttle to "off"
        elif self.X_button():
            self.throttle = 0 # set throttle to "50%"
        elif self.O_button():
            self.throttle = 1 # set throttle to "100%"
        return (self.throttle)
    def get_ail(self) -> float:
        self.ail_pressure, self.ail_last_pressed = update_hold_pressure_multi(
            self.ail_pressure, 
            self.right_button(), 
            self.left_button(), 
            self.ail_max_force, 
            self.ail_growth_rate, 
            self.ail_decay_rate, 
            self.ail_last_pressed
            )
        return self.ail_pressure

    def get_elev(self) -> float:
        self.elev_pressure, self.elev_last_pressed = update_hold_pressure_multi(
            self.elev_pressure, 
            self.up_button(), 
            self.down_button(), 
            self.elev_max_force, 
            self.elev_growth_rate, 
            self.elev_decay_rate, 
            self.elev_last_pressed
            )
        return self.elev_pressure

class Drum_Gimbal(SimGimbal): #working
    def __init__(self, joystick: pygame.joystick.Joystick):
        super().__init__(joystick)
        self.config = get_config()["Drum_Gimbal"]
        self.elev_pressure = 0.0
        self.elev_max_force = 1.0  # -1.0 to 1.0
        self.elev_growth_rate = 0.1
        self.elev_decay_rate = 0.05
        self.elev_hit_timestamps = []
        self.elev_hit_window = 1.0 # seconds
        self.elev_max_hits = 10 # hits per window
        self.ail_pressure = 0.0
        self.ail_max_force = 1.0  # -1.0 to 1.0
        self.ail_growth_rate = 0.1
        self.ail_decay_rate = 0.05
        self.ail_hit_timestamps = []
        self.ail_hit_window = 1.0 # seconds
        self.ail_max_hits = 10 # hits per window
        self.armed = 0 #throttle arming
        self.throttle = -1 # set throttle to "off"
    
    def red_pad(self):
        return self.joystick.get_button(2) #also circle
    def yellow_pad(self):
        return self.joystick.get_button(3) #also triangle
    def blue_pad(self):
        return self.joystick.get_button(0) #also square
    def green_pad(self):
        return self.joystick.get_button(1) #also X
    def kick_pedal(self):
        return self.joystick.get_button(4) #orange
    def select_button(self):
        return self.joystick.get_button(8)
    def home_button(self):
        return self.joystick.get_button(12)
    def start_button(self):
        return self.joystick.get_button(9)
    
    def get_throttle(self) -> float:
        if self.armed == 1:
            if self.select_button():
                self.throttle = -1 # set throttle to "off"
                self.armed = 0
            elif self.start_button():
                self.throttle = -1 # set throttle to "off"
                self.armed = 0
            elif self.kick_pedal() == 0:
                self.throttle = 0 # set throttle to "50%"
            elif self.kick_pedal() == 1:
                self.throttle = 1 # set throttle to "100%"
        else:
            if self.home_button():
                self.throttle = -1 # set throttle to "off"
                self.armed = 1

        return (self.throttle)
    
    def get_ail(self) -> float:
        self.ail_pressure = update_hit_pressure(
            self.ail_pressure,
            self.green_pad(), #right
            self.red_pad(), #left
            self.ail_max_force,
            self.ail_growth_rate,
            self.ail_decay_rate,
            self.ail_hit_timestamps,
            self.ail_hit_window,
            self.ail_max_hits
        )
        return self.ail_pressure
    def get_elev(self) -> float:
        self.elev_pressure = update_hit_pressure(
            self.elev_pressure,
            self.blue_pad(), #forwards
            self.yellow_pad(), #backwards
            self.elev_max_force,
            self.elev_growth_rate,
            self.elev_decay_rate,
            self.elev_hit_timestamps,
            self.elev_hit_window,
            self.elev_max_hits
        )
        return self.elev_pressure

class SteeringWheel_Gimbal(SimGimbal): #TODO
    def __init__(self, joystick: pygame.joystick.Joystick):
        super().__init__(joystick)
        self.config = get_config()["SteeringWheel_Gimbal"]

        self.armed = 0 #throttle arming
        self.throttle = -1 # set throttle to "off"

    def steering_wheel(self):
        return self.joystick.get_axis(self.config["steering"])
    def gas_brake_combo(self):
        return self.joystick.get_axis(self.config["gas_brake"])
    def gas_pedal(self):
        return self.joystick.get_axis(self.config["gas"])
    def brake_pedal(self):
        return self.joystick.get_axis(self.config["brake"])
    def right_paddle(self):
        return self.joystick.get_button(self.config["right_paddle"])
    def left_paddle(self):
        return self.joystick.get_button(self.config["left_paddle"])
    def select_button(self):
        return self.joystick.get_button(self.config["select"])
    def start_button(self):
        return self.joystick.get_button(self.config["start"])

    
    def get_throttle(self) -> float:
        if self.armed == 1:
            if self.select_button():
                self.throttle = -1 # set throttle to "off"
                self.armed = 0
            elif self.left_paddle() == 1:
                self.throttle = 0 # set throttle to "50%"
            elif self.right_paddle() == 1:
                self.throttle = 1 # set throttle to "100%"
        else:
            if self.start_button():
                self.throttle = -1 # set throttle to "off"
                self.armed = 1

        return (self.throttle)
    def get_ail(self) -> float:
        calibrated_ail = remap((self.steering_wheel()), -0.898, 0.884, -0.031, -1, 1, 0)
        return (calibrated_ail) #steering wheel
    def get_elev(self) -> float:
        if self.config["gas_brake"] is None: #linux doesn't have combined pedals
            gas_mid = ((self.config["gas_max"]-self.config["gas_min"])/2)+self.config["gas_min"]
            brake_mid = ((self.config["brake_max"]-self.config["brake_min"])/2)+self.config["brake_min"]
            calibrated_gas = remap(self.gas_pedal(), self.config["gas_min"], self.config["gas_max"], gas_mid , 0, 1, 0.5)
            calibrated_brake = remap(self.brake_pedal(), self.config["brake_min"], self.config["brake_max"], brake_mid , 0, -1, -0.5)
            return (calibrated_gas + calibrated_brake)
        
        else: #windows has combined gas and brake
            #def remap(num, inMin, inMax, inMid, outMin, outMax, outMid):
            calibrated_elev = remap((self.gas_brake_combo()), self.config["gas_brake_min"], self.config["gas_brake_max"], self.config["gas_brake_mid"], -1, 1, 0)
            return (calibrated_elev) #gas and brake pedal


#Right Gimbal for drive, Left Trigger for Weapon
class Xbox360_Gimbal(SimGimbal): #working
    def __init__(self, joystick: pygame.joystick.Joystick):
        super().__init__(joystick)
        self.config = get_config()["Xbox360_Gimbal"]

    def left_trigger(self):
        return self.joystick.get_axis(self.config["left_trigger"])
    def right_gimbal_LR(self):
        return self.joystick.get_axis(self.config["right_gimbal_LR"])
    def right_gimbal_UD(self):
        return (self.joystick.get_axis(self.config["right_gimbal_UD"])*-1)

    def get_throttle(self) -> float:
        return (self.left_trigger()) #L trigger
    def get_ail(self) -> float:
        return (self.right_gimbal_LR()) #R gimbal L/R
    def get_elev(self) -> float:
        return (self.right_gimbal_UD()) #R gimbal U/D

#Strum for Forwards/Backwards, 
class Guitar_Gimbal(SimGimbal): #working
    def __init__(self, joystick: pygame.joystick.Joystick):
        super().__init__(joystick)
        self.pressure = 0
        self.growth_rates = [0.1, 0.07, 0.05]  # Adjust speeds for smooth transitions
        self.max_forces = [0.5, 0.75, 1.0]  # Max pressures for each tier
        self.decay_rate = 0.03  # Rate of returning to 0
        self.last_direction = 0  # -1 for left, 1 for right, 0 for neutral
        self.elev_pressure = 0
        self.elev_max_force = 1.0
        self.elev_growth_rate = 0.1
        self.elev_decay_rate = 0.05
        self.throttle = -1 # set throttle to "off"

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
    def plus_button(self):
        return self.joystick.get_button(9)
    def minus_button(self):
        return self.joystick.get_button(8)

    def get_throttle(self) -> float:
        if self.orange_button():
            self.throttle = -1 # set throttle to "off"
        elif self.minus_button():
            self.throttle = 0 # set throttle to "50%"
        elif self.plus_button():
            self.throttle = 1 # set throttle to "100%"
        return (self.throttle)
    
    def get_ail(self):
        # Read button states
        green = self.green_button()
        red = self.red_button()
        yellow = self.yellow_button()
        blue = self.blue_button()

        # Track most recently pressed direction
        if red and not yellow:
            self.last_direction = -1  # Left
        elif yellow and not red:
            self.last_direction = 1  # Right

        # Resolve conflicting presses
        if red and yellow:
            if self.last_direction == -1:
                yellow = False  # Ignore yellow if red was pressed last
            else:
                red = False  # Ignore red if yellow was pressed last

        # Determine input levels
        if green and red:
            target_pressure = -self.max_forces[1]  # Slightly left
            growth_rate = self.growth_rates[1]
        elif green:
            target_pressure = -self.max_forces[2]  # Most left
            growth_rate = self.growth_rates[2]
        elif red:
            target_pressure = -self.max_forces[0]  # Least left
            growth_rate = self.growth_rates[0]
        elif yellow and blue:
            target_pressure = self.max_forces[1]  # Slightly right
            growth_rate = self.growth_rates[1]
        elif blue:
            target_pressure = self.max_forces[2]  # Most right
            growth_rate = self.growth_rates[2]
        elif yellow:
            target_pressure = self.max_forces[0]  # Least right
            growth_rate = self.growth_rates[0]
        else:
            target_pressure = 0
            growth_rate = self.decay_rate

        # Smoothly adjust pressure
        if self.pressure < target_pressure:
            self.pressure = min(target_pressure, self.pressure + growth_rate)
        elif self.pressure > target_pressure:
            self.pressure = max(target_pressure, self.pressure - growth_rate)

        return self.pressure
    def get_elev(self) -> float:
        self.elev_pressure = update_hold_pressure(
            self.elev_pressure, 
            (-1 == self.joystick.get_hat(0)[1]), 
            (1 == self.joystick.get_hat(0)[1]), 
            self.elev_max_force, 
            self.elev_growth_rate, 
            self.elev_decay_rate
            )
        return self.elev_pressure
        #return (self.joystick.get_hat(0)[1]*-1) #strum down = forward, up=backwards

class KeyboardMouse_Gimbal(SimGimbal): #TODO
    def get_throttle(self) -> float:
        return (4)
    def get_ail(self) -> float:
        return (self.joystick.get_button(0) + 0.1)
    def get_elev(self) -> float:
        return (self.joystick.get_button(0) + 0.1)

def gimbal_factory(joystick: pygame.joystick.Joystick) -> SimGimbal:
    joystick_name = joystick.get_name().lower()
    #print("Factory Name: ", joystick_name)
    if "gamepad" in joystick_name: #USB Gamepad
        return DDRPad_Gimbal(joystick)
    elif "drum" in joystick_name: #Licensed by Sony Computer Entertainment America Harmonix Drum Kit for PlayStation(R)3
        return Drum_Gimbal(joystick)
    elif "windows" in joystick_name: #MY-POWER CO.,LTD Controller For Windows
        return Guitar_Gimbal(joystick)
    elif "driving" in joystick_name:
        return SteeringWheel_Gimbal(joystick)
    elif "xbox" in joystick_name:
        return Xbox360_Gimbal(joystick) #Xbox 360 Controller
    else:
        return KeyboardMouse_Gimbal(joystick)

pygame.init()
pygame.joystick.init()
screen = pygame.display.set_mode((500, 700),pygame.RESIZABLE)
clock = pygame.time.Clock()
font = pygame.font.Font(None, 24)
joysticks = {}
gimbals = {}
running = True

while running:
    screen.fill((255, 255, 255))
    y_offset = 10
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.JOYDEVICEADDED:
            joystick = pygame.joystick.Joystick(event.device_index)
            joysticks[joystick.get_instance_id()] = joystick
            gimbals[joystick.get_instance_id()] = gimbal_factory(joystick)
        
        if event.type == pygame.JOYDEVICEREMOVED:
            if event.instance_id in joysticks:
                del joysticks[event.instance_id]
            if event.instance_id in gimbals:
                del gimbals[event.instance_id]
    
    for jid, joystick in joysticks.items():
        gimbal = gimbals[jid]
        jname = joystick.get_name()
        text_title = font.render(f"Joystick {jid}: {jname}", True, (0, 0, 0))
        screen.blit(text_title, (10, y_offset))
        y_offset += 20
        if (jname == "3Dconnexion KMJ Emulator") or (jname == "SpaceNavigator"): #Hide 3D mouse outputs
            pass
        else:
            # Display Gimbal values
            text_surface = font.render(f"Gimbals -> Throttle: {gimbal.get_throttle():.3f}, Ail: {gimbal.get_ail():.3f}, Elev: {gimbal.get_elev():.3f}", True, (0, 0, 0))
            screen.blit(text_surface, (10, y_offset))
            y_offset += 20
            # Display raw axis values
            axes = joystick.get_numaxes()
            for i in range(axes):
                axis_value = joystick.get_axis(i)
                axis_surface = font.render(f"Axis {i}: {axis_value:.3f}", True, (0, 0, 0))
                screen.blit(axis_surface, (10, y_offset))
                y_offset += 20
            
            # Display button states
            buttons = joystick.get_numbuttons()
            for i in range(buttons):
                button_value = joystick.get_button(i)
                button_surface = font.render(f"Button {i}: {button_value}", True, (0, 0, 0))
                screen.blit(button_surface, (10, y_offset))
                y_offset += 20
            
            # Display hat switch states
            hats = joystick.get_numhats()
            for i in range(hats):
                hat_value = joystick.get_hat(i)
                hat_surface = font.render(f"Hat {i}: {hat_value}", True, (0, 0, 0))
                screen.blit(hat_surface, (10, y_offset))
                y_offset += 30
    
    pygame.display.flip()
    clock.tick(30)

pygame.quit()
