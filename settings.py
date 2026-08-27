# settings.py
from typing import Any

# Fenster-Einstellungen
DEFAULT_SCREEN_WIDTH = 800
DEFAULT_SCREEN_HEIGHT = 600
SCREEN_WIDTH = DEFAULT_SCREEN_WIDTH
SCREEN_HEIGHT = DEFAULT_SCREEN_HEIGHT
BLOCK_WIDTH = 60
BLOCK_HEIGHT = 30
BALL_SPEED = 5.5
FPS = 60
TITLE = "Danis Breakout"

# Farben (R, G, B)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
REDDISH_ORANGE = (255, 86, 56)
ORANGE = (255, 133, 0)
ORANGE_YELLOW = (255, 172, 56)
YELLOW = (255, 255, 0)
PURPLE = (195, 56, 255)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
DARK_GREY = (40, 40, 40)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
STEEL_GREY = (120, 130, 140)
DARK_PURPLE = (100, 20, 140)

# Difficulty Levels
DIFFICULTY_EASY = "EASY"
DIFFICULTY_NORMAL = "NORMAL"
DIFFICULTY_HARD = "HARD"

DIFFICULTY_SETTINGS: dict[str, dict[str, Any]] = {
    DIFFICULTY_EASY: {
        "label": "Einfach",
        "ball_speed_mult": 0.8,
        "powerup_chance": 0.25,
        "timer_mult": 1.2,
    },
    DIFFICULTY_NORMAL: {
        "label": "Normal",
        "ball_speed_mult": 1.0,
        "powerup_chance": 0.15,
        "timer_mult": 1.0,
    },
    DIFFICULTY_HARD: {
        "label": "Schwer",
        "ball_speed_mult": 1.2,
        "powerup_chance": 0.10,
        "timer_mult": 0.8,
    }
}

# Game States (Zustände)
STATE_MENU = "MENU"
STATE_PLAYING = "PLAYING"
STATE_PAUSED = "PAUSED"
STATE_GAME_OVER = "GAME_OVER"
STATE_LEVEL_CLEARED = "LEVEL_CLEARED"
STATE_LEVEL_SELECT = "LEVEL_SELECT"
STATE_EDITOR = "EDITOR"
STATE_HIGHSCORE = "HIGHSCORE"
STATE_SETTINGS = "SETTINGS"
STATE_ALL_CLEARED = "ALL_CLEARED"
