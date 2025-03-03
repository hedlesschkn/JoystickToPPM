import pygame
import time
from abc import ABC, abstractmethod

# Constants for hit-based pressure
HIT_WINDOW = 1.0  # Seconds to track hits
MAX_HITS = 10     # Maximum hits per second for full pressure

# Tracking hit timestamps
hit_timestamps = []

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

def update_hit_pressure():
    now = time.time()
    hit_timestamps[:] = [t for t in hit_timestamps if now - t <= HIT_WINDOW]
    return min(1.0, len(hit_timestamps) / MAX_HITS)

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
        text_surface = font.render(f"Joystick {jid} -> Throttle: {gimbal.get_throttle():.3f}, Ail: {gimbal.get_ail():.3f}, Elev: {gimbal.get_elev():.3f}", True, (0, 0, 0))
        screen.blit(text_surface, (10, y_offset))
        y_offset += 30
        
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
            y_offset += 20
    
    pygame.display.flip()
    clock.tick(30)

pygame.quit()
