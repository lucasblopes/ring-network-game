# settings.py
import os

# Game configs
EMOJIS = True
NUM_CARDS = 4
LIVES = 3
NUM_PLAYERS = 4

# Network config
BUFFER_SIZE = 1024
HOSTS = ["127.0.0.1", "127.0.0.1", "127.0.0.1", "127.0.0.1"]  # IPs dos jogadores
PORTS = [5000, 5001, 5002, 5003]  # Portas dos jogadores

# Misc
if EMOJIS:
    SUIT_EMOJIS = {"H": "󰋑", "D": "󰣏", "C": "󰣎", "S": "󰣑"}
else:
    SUIT_EMOJIS = {"H": "(Hearts)", "D": "(Diamonds)", "C": "(Clubs)", "S": "(Spades)"}


def clear_screen():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")
