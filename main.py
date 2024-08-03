import sys
import os
from ring_network import Network
from game import Game
from settings import clear_screen


def main():
    try:
        clear_screen()
        player_id = int(sys.argv[1])
        network = Network(player_id)
        game = Game(player_id, network)
        game.start()
    except IndexError:
        print("Usage: python main.py <player_id>")
    except Exception as e:
        print(f"Error starting game: {e}")


if __name__ == "__main__":
    main()

