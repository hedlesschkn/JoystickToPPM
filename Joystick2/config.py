# config.py
# import os
import platform
import logging
logger = logging.getLogger(__name__)

# print(platform.system().lower())

config_windows = {
    "DDRPad_Gimbal": {
    "up": 0,
    "down": 1,
    "left": 2,
    "right": 3,
    "X": 6,
    "O": 7,
    "back": 8,
    "select": 9,
    },
    "Drum_Gimbal": {
    "red": 2,
    "circle": 2,
    "yellow": 3,
    "triangle": 3,
    "blue": 0,
    "square": 0,
    "green": 1,
    "X": 1,
    "kick": 4,
    "select": 8,
    "home": 12,
    "start": 9,
    },
    "SteeringWheel_Gimbal": {
    "steering": 0,
    "gas": None,
    "brake": None,
    "gas_brake": 1,
    "gas_brake_min": 0.413,
    "gas_brake_max": -0.695,
    "gas_brake_mid": -0.164,
    "right_paddle": 10,
    "left_paddle": 11,
    "select": 8,
    "start": 9,
    },
    "Xbox360_Gimbal": {
    "left_trigger": 4,
    "right_gimbal_LR": 2,
    "right_gimbal_UD": 3,
    },
    "Guitar_Gimbal": {
    "green": 1,
    "red": 0,
    "yellow": 3,
    "blue": 2,
    "orange": 6,
    "plus": 9,
    "minus": 8,
    "strum": 0 #hat
    }
}

config_linux = {
    "DDRPad_Gimbal": { #same
    "up": 0,
    "down": 1,
    "left": 2,
    "right": 3,
    "X": 6,
    "O": 7,
    "back": 8,
    "select": 9,
    },
    "Drum_Gimbal": { #same
    "red": 2,
    "circle": 2,
    "yellow": 3,
    "triangle": 3,
    "blue": 0,
    "square": 0,
    "green": 1,
    "X": 1,
    "kick": 4,
    "select": 8,
    "home": 12,
    "start": 9,
    },
    "SteeringWheel_Gimbal": {
    "steering": 0,
    "gas_brake": None,
    "gas": 1,
    "gas_min": 0.357,
    "gas_max": -0.725,
    "brake": 2,
    "brake_min": 0.584,
    "brake_max": -0.561,
    "right_paddle": 10,
    "left_paddle": 11,
    "select": 8,
    "start": 9,
    },
    "Xbox360_Gimbal": { #done
    "left_trigger": 2,
    "right_gimbal_LR": 3,
    "right_gimbal_UD": 4,
    },
    "Guitar_Gimbal": { #same
    "green": 1,
    "red": 0,
    "yellow": 3,
    "blue": 2,
    "orange": 6,
    "plus": 9,
    "minus": 8,
    "strum": 0 #hat
    }
}

config_macos = { #todo
  "guitar": {
    "red": 4,
  },
  "drum": {
    "red": 0
  }
}
# # Detect the OS
# def get_system():
#     os_name = platform.system()
#     if os_name == "Windows":
#         return "Windows"
#     elif os_name == "Linux":
#         # Further check if it's a Raspberry Pi
#         try:
#             with open("/sys/firmware/devicetree/base/model", "r") as f:
#                 if "Raspberry Pi" in f.read():
#                     return "Raspbian"
#         except FileNotFoundError:
#             pass
#     return "Unknown"

def get_config():
    if platform.system().lower() == "windows":
        return config_windows
    elif platform.system().lower() == "darwin":
        return config_macos
    elif platform.system().lower() == "linux":
        return config_linux
    else:
        # or raise an exception
        return config_linux

def get_GPIO():
    if platform.system().lower() == "windows":
        logging.warning("pigpio library not availale on Windows, running in debug mode")
        return False
    elif platform.system().lower() == "darwin":
        logging.warning("pigpio library not availale on MacOS, running in debug mode")
        return False
    elif platform.system().lower() == "linux":
        try:
          import pigpio
          return True
        except ImportError as e:
            logging.warning(e, exc_info=True)
            logging.warning("Failed to load pigpio library, running in debug mode")
            return False
    else:
        # or raise an exception
        return False