# config.py
# import os
import platform

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
    "gas_brake": 1,
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
    }
}

config_linux = {
  "guitar": {
    "red": 4,
  },
  "drum": {
    "red": 0
  }
}

config_macos = {
  "guitar": {
    "red": 4,
  },
  "drum": {
    "red": 0
  }
}


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