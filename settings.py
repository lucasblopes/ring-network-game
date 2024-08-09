# settings.py
import os

# Game configs
EMOJIS = True
NUM_CARDS = 2
LIVES = 1
NUM_PLAYERS = 4

# Network config
BUFFER_SIZE = 1024
# HOSTS = ["127.0.0.1", "127.0.0.1", "127.0.0.1", "127.0.0.1"]  # IPs dos jogadores
HOSTS = [
    "200.17.202.34",  # cpu1
    "200.17.202.35",  # cpu2
    "200.17.202.98",  # zara
    "200.17.202.7",  # orval
]
PORTS = [5000, 5001, 5002, 5004]  # Portas dos jogadores

# Misc
if EMOJIS:
    SUIT_EMOJIS = {"D": "󰣏", "S": "󰣑", "H": "󰋑", "C": "󰣎"}
else:
    SUIT_EMOJIS = {"D": "(Diamonds)", "S": "(Spades)", "H": "(Hearts)", "C": "(Clubs)"}


def clear_screen():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")
