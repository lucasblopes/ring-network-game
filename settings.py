# settings.py
import os

BUFFER_SIZE = 1024
NUM_PLAYERS = 4
HOSTS = ["127.0.0.1", "127.0.0.1", "127.0.0.1", "127.0.0.1"]  # IPs dos jogadores
PORTS = [5000, 5001, 5002, 5003]  # Portas dos jogadores
NUM_CARDS = 4
LIVES = 3
SUIT_EMOJIS = {"Hearts": "󰋑", "Diamonds": "󰣏", "Clubs": "󰣎", "Spades": "󰣑"}


def clear_screen():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")
