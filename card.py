from settings import SUIT_EMOJIS


class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def __str__(self):
        return f"{self.rank}-{self.suit}"

    def print_card(self):
        return f"{self.rank} {SUIT_EMOJIS[self.suit]}"
