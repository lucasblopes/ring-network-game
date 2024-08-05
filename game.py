import random
from settings import NUM_PLAYERS, NUM_CARDS, LIVES, SUIT_EMOJIS, clear_screen
from tabulate import tabulate
from colorama import init, Fore, Style

# Initialize colorama
init()

SUITS = ["Hearts", "Diamonds", "Clubs", "Spades"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

# Actions
NEW_DEALER = 1
DEAL_CARDS = 2
ASK_BETS = 3
SHOW_BETS = 4
ASK_CARD = 5
RESULTS = 6
UPDATE_SCOREBOARD = 7


class Game:
    def __init__(self, player_id, network):
        self.player_id = player_id
        self.next_player_id = (player_id + 1) % NUM_PLAYERS
        self.network = network
        self.is_dealer = player_id == 0
        self.lives = [LIVES] * NUM_PLAYERS
        self.hands = [[] for _ in range(NUM_PLAYERS)]
        self.bets = [-1] * NUM_PLAYERS
        self.deck = []
        self.played_cards = [""] * NUM_PLAYERS  # Track played cards

    def create_deck(self):
        self.deck = [{"suit": suit, "rank": rank} for suit in SUITS for rank in RANKS]
        random.shuffle(self.deck)

    def deal_cards(self):
        input("Press ENTER to deal cards...")
        for i in range(NUM_PLAYERS):
            self.hands[i] = [self.deck.pop() for _ in range(NUM_CARDS)]
        print(f"Player {self.player_id} dealt cards.")
        self.update_display()

        for i in range(NUM_PLAYERS):
            if i != self.player_id:
                data = ",".join(
                    [f"{card['rank']}-{card['suit']}" for card in self.hands[i]]
                )
                self.network.send(self.player_id, i, DEAL_CARDS, data)

    def print_hand(self):
        hand_table = [
            [index, f"{card['rank']} {SUIT_EMOJIS[card['suit']]}"]
            for index, card in enumerate(self.hands[self.player_id])
        ]
        print(
            Fore.CYAN + "\n Player {}'s hand:".format(self.player_id) + Style.RESET_ALL
        )
        print(
            tabulate(
                hand_table,
                headers=[
                    Fore.YELLOW + "Index" + Style.RESET_ALL,
                    Fore.YELLOW + "Card" + Style.RESET_ALL,
                ],
                tablefmt="fancy_grid",
            )
        )

    def print_scoreboard(self):
        scoreboard_table = [
            [
                f"Player {i}",
                f"{life} {SUIT_EMOJIS['Hearts']}",
                f"Bet: {' ' if bet == -1 else bet}",
                f"Card: {self.played_cards[i]}",
            ]
            for i, (life, bet) in enumerate(zip(self.lives, self.bets))
        ]
        print(Fore.CYAN + "\n Scoreboard:" + Style.RESET_ALL)
        print(
            tabulate(
                scoreboard_table,
                headers=[
                    Fore.YELLOW + "Player" + Style.RESET_ALL,
                    Fore.YELLOW + "Lives" + Style.RESET_ALL,
                    Fore.YELLOW + "Bet" + Style.RESET_ALL,
                    Fore.YELLOW + "Played Card" + Style.RESET_ALL,
                ],
                tablefmt="fancy_grid",
            )
        )

    def update_scoreboard(self):
        lives_data = ",".join([str(life) for life in self.lives])
        self.network.send(
            self.player_id,
            self.next_player_id,
            UPDATE_SCOREBOARD,
            lives_data,
        )

    def update_display(self):
        clear_screen()
        self.print_scoreboard()
        self.print_hand()

    def start(self):
        print(
            Fore.GREEN + "Player" + Style.RESET_ALL,
            self.player_id,
            Fore.GREEN + "joined the game!" + Style.RESET_ALL,
        )
        if self.is_dealer:
            input(
                Fore.YELLOW
                + "Press ENTER to shuffle the cards after all players are online!..."
                + Style.RESET_ALL
            )
            self.create_deck()
            print(Fore.YELLOW + "Cards have been shuffled!..." + Style.RESET_ALL)
            self.deal_cards()
            self.ask_for_bets()

        while True:
            message = self.network.receive()
            if message:
                self.process_game_message(message)
                if message["destination"] != self.player_id:
                    self.network.send(
                        message["source"],
                        message["destination"],
                        message["action"],
                        message["data"],
                    )
                self.update_display()

    def ask_for_bets(self):
        if self.is_dealer:
            self.update_display()
            bet = self.get_valid_bet()
            self.bets[self.player_id] = bet
            bet_data = f"{self.player_id}-{bet}"
            self.network.send(self.player_id, self.next_player_id, ASK_BETS, bet_data)
        self.update_display()

    def place_bet(self, player_id, bet):
        self.bets[player_id] = bet
        if all(
            bet != -1 for bet in self.bets
        ):  # Check if all players have placed their bets
            self.show_bets()
        self.update_display()

    def show_bets(self):
        if self.is_dealer:
            bets_data = ",".join([f"{i}-{self.bets[i]}" for i in range(NUM_PLAYERS)])
            self.network.send(self.player_id, self.next_player_id, SHOW_BETS, bets_data)
        self.update_display()

    def ask_for_cards(self):
        if self.is_dealer:
            clear_screen()
            print(Fore.YELLOW + "Starting the game..." + Style.RESET_ALL)
            self.print_hand()
            card_index = self.get_valid_card_index()
            card = self.hands[self.player_id][card_index]
            print(
                f"Player {self.player_id} chose card {card['rank']} {SUIT_EMOJIS[card['suit']]}"
            )
            card_data = f"{self.player_id}-{self.hands[self.player_id][card_index]['rank']}-{self.hands[self.player_id][card_index]['suit']}"
            self.hands[self.player_id].pop(card_index)
            self.played_cards[self.player_id] = (
                f"{card['rank']} {SUIT_EMOJIS[card['suit']]}"
            )
            self.network.send(self.player_id, self.next_player_id, ASK_CARD, card_data)
        self.update_display()

    def get_valid_card_index(self):
        while True:
            self.update_display()
            try:
                card_index = int(
                    input(
                        Fore.MAGENTA
                        + f"Player {self.player_id}, choose a card by index: "
                        + Style.RESET_ALL
                    )
                )
                if 0 <= card_index < len(self.hands[self.player_id]):
                    return card_index
                else:
                    print(
                        Fore.RED
                        + "Invalid index. Please choose a valid card index."
                        + Style.RESET_ALL
                    )
            except ValueError:
                print(
                    Fore.RED + "Invalid input. Please enter a number." + Style.RESET_ALL
                )

    def handle_round_end(self, card_data):
        print(Fore.GREEN + "Round ended. Cards played:" + Style.RESET_ALL, card_data)
        self.compute_round_results(card_data)
        self.start_next_round()
        self.update_display()

    # implementar
    def compute_round_results(self, card_data):
        pass

    # implementar
    def start_next_round(self):
        pass

    def process_game_message(self, message):
        action = message["action"]
        handlers = {
            DEAL_CARDS: self.handle_deal_cards,
            ASK_BETS: self.handle_ask_bet,
            SHOW_BETS: self.handle_show_bets,
            ASK_CARD: self.handle_ask_card,
            NEW_DEALER: self.handle_new_dealer,
            UPDATE_SCOREBOARD: self.handle_update_scoreboard,
        }

        handler = handlers.get(action)
        if handler:
            handler(message)

    def handle_deal_cards(self, message):
        if message["destination"] == self.player_id and not self.is_dealer:
            self.hands[self.player_id] = [
                {"rank": card.split("-")[0], "suit": card.split("-")[1]}
                for card in message["data"].split(",")
            ]
            self.print_hand()
        self.update_display()

    def get_valid_bet(self):
        while True:
            self.update_display()
            try:
                bet = int(
                    input(
                        Fore.MAGENTA
                        + f"Player {self.player_id}, enter your bet: "
                        + Style.RESET_ALL
                    )
                )
                if 0 <= bet < len(self.hands[self.player_id]):
                    return bet
                else:
                    print(
                        Fore.RED
                        + "Invalid bet. Please choose a valid bet."
                        + Style.RESET_ALL
                    )
            except ValueError:
                print(
                    Fore.RED + "Invalid input. Please enter a number." + Style.RESET_ALL
                )

    def handle_ask_bet(self, message):
        bet_info = message["data"].split(",")
        for bet in bet_info:
            player, amount = map(int, bet.split("-"))
            self.bets[player] = amount

        if self.bets[self.player_id] == -1:  # Check if this player has placed a bet
            bet = self.get_valid_bet()
            self.bets[self.player_id] = bet
            bet_info.append(f"{self.player_id}-{bet}")

        if self.is_dealer:
            self.show_bets()
        else:
            self.network.send(
                self.player_id,
                self.next_player_id,
                ASK_BETS,
                ",".join(bet_info),
            )
        self.update_display()

    def handle_show_bets(self, message):
        print(Fore.GREEN + f"Bets: {message['data']}" + Style.RESET_ALL)
        if self.is_dealer:
            self.ask_for_cards()
        else:
            self.network.send(
                message["source"], self.next_player_id, SHOW_BETS, message["data"]
            )
        self.update_display()

    def handle_ask_card(self, message):
        card_info = message["data"].split(",")
        for card in card_info:
            player, rank, suit = card.split("-")
            self.played_cards[int(player)] = f"{rank} {SUIT_EMOJIS[suit]}"

        if self.played_cards[self.player_id] == "":
            print("Your hand:")
            self.print_hand()
            card_index = self.get_valid_card_index()
            card = self.hands[self.player_id].pop(card_index)
            card_info.append(f"{self.player_id}-{card['rank']}-{card['suit']}")
            self.played_cards[self.player_id] = (
                f"{card['rank']} {SUIT_EMOJIS[card['suit']]}"
            )

        if all(card != "" for card in self.played_cards):
            if self.is_dealer:
                print(
                    Fore.GREEN
                    + "All players have played their cards."
                    + Style.RESET_ALL
                )
                self.handle_round_end(",".join(card_info))
            else:
                self.network.send(
                    self.player_id, self.next_player_id, ASK_CARD, ",".join(card_info)
                )
        else:
            self.network.send(
                self.player_id, self.next_player_id, ASK_CARD, ",".join(card_info)
            )
        self.update_display()

    # implementar
    def handle_new_dealer(self, message):
        pass

    # implementar
    def handle_update_scoreboard(self, message):
        pass

