import random
from settings import NUM_PLAYERS, NUM_CARDS, LIVES, SUIT_EMOJIS, clear_screen
from card import Card
from tabulate import tabulate
from colorama import init, Fore, Style

# Initialize colorama
init()

# Cartas do Truco
SUITS = ["D", "S", "H", "C"]
RANKS = ["4", "5", "6", "7", "Q", "J", "K", "A", "2", "3"]

# Actions
NEW_DEALER = 1
DEAL_CARDS = 2
ASK_BETS = 3
SHOW_BETS = 4
ASK_CARD = 5
ROUND_RESULTS = 6
HAND_RESULTS = 7
PLAYER_WON = 8


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
        self.points = [0] * NUM_PLAYERS  # Track points of each player

    def print_scoreboard(self):
        scoreboard_table = [
            [
                f"Player {i}",
                f"{life} {SUIT_EMOJIS['H']}",
                f"Bet: {' ' if bet == -1 else bet}",
                f"Card: {' ' if not self.played_cards[i] else Card(self.played_cards[i].split('-')[0], self.played_cards[i].split('-')[1]).print_card()}",
                f"Points: {self.points[i]}",
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
                    Fore.YELLOW + "Points" + Style.RESET_ALL,
                ],
                tablefmt="fancy_grid",
            )
        )

    def print_hand(self):
        if self.lives[self.player_id] < 1:
            return
        hand_table = [
            [index, card.print_card()]
            for index, card in enumerate(self.hands[self.player_id])
        ]
        print(Fore.CYAN + f"\n Player {self.player_id}'s hand:" + Style.RESET_ALL)
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

    def update_display(self):
        clear_screen()
        self.print_scoreboard()
        self.print_hand()

    def create_deck(self):
        self.deck = [Card(rank, suit) for suit in SUITS for rank in RANKS]
        random.shuffle(self.deck)

    def deal_cards(self):
        input("Press ENTER to deal cards...")
        for i in range(NUM_PLAYERS):
            if (self.lives[i] > 0):
                self.hands[i] = [self.deck.pop() for _ in range(NUM_CARDS)]
        print(f"Player {self.player_id} dealt cards.")
        self.update_display()

        for i in range(NUM_PLAYERS):
            if i != self.player_id:
                cards_data = ",".join(str(card) for card in self.hands[i])
                self.network.send(self.player_id, i, DEAL_CARDS, cards_data)
                self.network.receive()
    
    def check_winner(self):
        players = 0
        index = 0
        for i in range(NUM_PLAYERS):
            if self.lives[i] > 0:
                index = i
                players+=1
        if players == 1:
            self.network.send(self.player_id, self.next_player_id, PLAYER_WON, index)
            self.update_display()
            return True
        return False

    def start(self):
        print(
            Fore.GREEN + "Player" + Style.RESET_ALL,
            self.player_id,
            Fore.GREEN + "joined the game!" + Style.RESET_ALL,
        )
        if self.is_dealer:
            input(
                Fore.YELLOW
                + "Press ENTER to shuffle the cards when all players are ready!..."
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
                self.update_display()

    def ask_for_bets(self):
        bet_data = ""
        if self.is_dealer and self.lives[self.player_id] > 0:
            self.update_display()
            bet = self.get_valid_bet()
            self.bets[self.player_id] = bet
            bet_data = f"{self.player_id}-{bet}"
        self.network.send(self.player_id, self.next_player_id, ASK_BETS, bet_data)
        self.update_display()

    def show_bets(self):
        bets = []
        if self.is_dealer:
            for i in range(NUM_PLAYERS):
                if self.lives[i] > 0:
                    bet = f"{i}-{self.bets[i]}"
                    bets.append(bet)
            self.network.send(self.player_id, self.next_player_id, SHOW_BETS, ",".join(bets))
        self.update_display()

    def ask_for_cards(self):
        if self.is_dealer:
            clear_screen()
            print(Fore.YELLOW + "Starting the game..." + Style.RESET_ALL)
            card_data = ""
            if self.lives[self.player_id] > 0:
                self.print_hand()
                card_index = self.get_valid_card_index()
                card = self.hands[self.player_id][card_index]
                print(f"Player {self.player_id} chose card {card.print_card()}")
                card_data = f"{self.player_id}-{card}"
                self.hands[self.player_id].pop(card_index)
                self.played_cards[self.player_id] = str(card)
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
                    input(
                        Fore.RED
                        + "Invalid index. Please choose a valid card index."
                        + Style.RESET_ALL
                    )
            except ValueError:
                input(
                    Fore.RED + "Invalid input. Please enter a number." + Style.RESET_ALL
                )

    def handle_round_end(self):
        if self.is_dealer:
            print(Fore.GREEN + "All players have played their cards.")
            input(Fore.GREEN + "Press ENTER to compute the round results...")
            self.compute_round_results()
            self.update_display()

    def compute_round_results(self):
        if self.is_dealer:
            # Initialize with player card 0
            highest_card = Card("4","D")
            highest_player = -1

            for i, card_str in enumerate(self.played_cards):
                if (card_str == ""): continue
                rank, suit = card_str.split("-")
                card = Card(rank, suit)
                # Obs.: If two players have the exactly same card, the last that played, wins
                if RANKS.index(card.rank) > RANKS.index(highest_card.rank) or (
                    RANKS.index(card.rank) == RANKS.index(highest_card.rank)
                    and SUITS.index(card.suit) >= SUITS.index(highest_card.suit)
                ):
                    highest_card = card
                    highest_player = i

            self.points[highest_player] += 1
            print(
                Fore.YELLOW
                + f"Player {highest_player} wins the round with {highest_card.print_card()}!"
                + Style.RESET_ALL
            )
            input(Fore.GREEN + "Press ENTER to continue..." + Style.RESET_ALL)

            # Prepare the card data with winner/loser information
            card_data = []
            for i, card_str in enumerate(self.played_cards):
                if (card_str == ""): continue
                rank, suit = card_str.split("-")
                card = Card(rank, suit)
                status = "w" if i == highest_player else "l"
                card_data.append(f"{i}-{card}-{status}")

            # Send message to the network about the round winner
            self.network.send(
                self.player_id, self.next_player_id, ROUND_RESULTS, ",".join(card_data)
            )

            # Reset played cards for next round
            self.played_cards = [""] * NUM_PLAYERS

    # palyer-bet-points-lives
    def calculate_hand_results(self):
        data = []
        for i in range(NUM_PLAYERS) :
            if (self.lives[i] <= 0): continue
            lives_lost = abs(self.points[i] - self.bets[i])
            self.lives[i] -= lives_lost
            data.append(f"{i}-{self.bets[i]}-{self.points[i]}-{self.lives[i]}")
            if (self.lives[i] > 0) :
                print(
                        Fore.YELLOW
                        + f"Player {i} bet {self.bets[i]} and got {self.points[i]}. He has now {self.lives[i]} lifes"
                        + Style.RESET_ALL
                    )
            else:
                print(
                        Fore.RED
                        + f"Player {i} bet {self.bets[i]} and got {self.points[i]} and is out of the game!"
                        + Style.RESET_ALL
                    )
                self.points[i] = ""
            self.bets[i] = -1
            self.points[i] = 0

        input(Fore.GREEN + "Press ENTER to continue..." + Style.RESET_ALL)
        self.update_display()
        self.network.send(
                self.player_id, self.next_player_id, HAND_RESULTS, ",".join(data)
            )
            

    def process_game_message(self, message):
        action = message["action"]
        handlers = {
            DEAL_CARDS: self.handle_deal_cards,
            ASK_BETS: self.handle_ask_bet,
            SHOW_BETS: self.handle_show_bets,
            ASK_CARD: self.handle_ask_card,
            ROUND_RESULTS: self.handle_round_results,
            HAND_RESULTS: self.handle_hand_results,
            NEW_DEALER: self.handle_new_dealer,
            PLAYER_WON: self.handle_player_won,
        }
        handler = handlers.get(action)
        if handler:
            handler(message)

    def handle_deal_cards(self, message):
        if self.is_dealer:
            return
        if message["destination"] == self.player_id and not self.is_dealer and self.lives[self.player_id] > 0:
            card_data = message["data"].split(",")
            self.hands[self.player_id] = [
                Card(card.split("-")[0], card.split("-")[1]) for card in card_data
            ]
        self.network.send(message["source"],
                    message["destination"],
                    message["action"],
                    message["data"],
                )
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
                if 0 <= bet <= len(self.hands[self.player_id]):
                    return bet
                else:
                    input(
                        Fore.RED
                        + "Invalid bet. Please choose a valid bet."
                        + Style.RESET_ALL
                    )
            except ValueError:
                input(
                    Fore.RED + "Invalid input. Please enter a number." + Style.RESET_ALL
                )

    def handle_ask_bet(self, message):
        bet_info = []
        if message["data"] != "":
            bet_info = message["data"].split(",")
            for bet in bet_info:
                player, amount = map(int, bet.split("-"))
                self.bets[player] = amount

        if self.lives[self.player_id] > 0 and self.bets[self.player_id] == -1:  # Check if this player has placed a bet
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
            bet_info = message["data"].split(",")
            for bet in bet_info:
                player, amount = map(int, bet.split("-"))
                self.bets[player] = amount
            self.network.send(
                self.player_id, self.next_player_id, SHOW_BETS, message["data"]
            )
        self.update_display()

    def handle_ask_card(self, message):
        card_info = []
        if message["data"] != "" :
            card_info = message["data"].split(",")
            for card_str in card_info:
                player_id, rank, suit = card_str.split("-")
                card = Card(rank, suit)
                self.played_cards[int(player_id)] = str(card)

        self.update_display()
        if self.played_cards[self.player_id] == "" and self.lives[self.player_id] > 0:
            self.print_hand()
            card_index = self.get_valid_card_index()
            card = self.hands[self.player_id].pop(card_index)
            self.played_cards[self.player_id] = str(card)
            card_info.append(f"{self.player_id}-{str(card)}")

        if self.is_dealer:
            self.handle_round_end()
        else:
            self.network.send(
                self.player_id, self.next_player_id, ASK_CARD, ",".join(card_info)
            )

    # implementar
    def handle_round_results(self, message):
        if self.is_dealer:
            if (len(self.hands[self.player_id]) == 0):
                self.calculate_hand_results()
            else:
                self.played_cards = [""] * NUM_PLAYERS
                self.update_display()
                self.ask_for_cards()
            return

        # Atualizar o placar
        round_results = message["data"].split(",")
        card = None
        winner_id = -1
        winner_card = ["", ""]

        for result in round_results:
            player_id, rank, suit, status = result.split("-")
            card = Card(rank, suit)
            self.played_cards[int(player_id)] = str(card)
            if status == "w":
                winner_id = player_id
                winner_card = card
                self.points[int(player_id)] += 1

        self.update_display()
        if winner_id != -1:
            if card:
                print(
                    Fore.YELLOW
                    + f"Player {winner_id} wins the round with {winner_card.print_card()}!"
                    + Style.RESET_ALL
                )
                input(Fore.GREEN + "Press ENTER to continue..." + Style.RESET_ALL)
            else:
                exit(1)

        # Resetar as cartas jogadas
        self.played_cards = [""] * NUM_PLAYERS
        self.update_display()
        self.network.send(
            self.player_id, self.next_player_id, ROUND_RESULTS, message["data"]
        )

    # implementar
    def handle_hand_results(self, message):
        if self.is_dealer:
            print(
                Fore.GREEN
                + "Not the dealer anymore, passing baton"
                + Style.RESET_ALL
            )
            input(Fore.GREEN + "Press ENTER to continue..." + Style.RESET_ALL)
            self.network.send(
                self.player_id, self.next_player_id, NEW_DEALER, ""
            )
            self.update_display()
            self.is_dealer = False
            return
        
        data = message["data"].split(",")
        for player_data in data:
            player_data = player_data.split("-")
            player_id = int(player_data[0])
            player_lives = int(player_data[3])
            self.lives[player_id] = player_lives
            self.bets[player_id] = -1
            self.points[player_id] = 0
            if (player_lives > 0) :
                print(
                        Fore.YELLOW
                        + f"Player {player_id} bet {player_data[1]} and got {player_data[2]}. He has now {player_lives} lifes"
                        + Style.RESET_ALL
                    )
            else:
                print(
                        Fore.RED
                        + f"Player {player_id} bet {player_data[1]} and got {player_data[2]} and is out of the game!"
                        + Style.RESET_ALL
                    )
                self.points[player_id] = ""
        input(Fore.GREEN + "Press ENTER to continue..." + Style.RESET_ALL)
        self.update_display()
        self.network.send(
                self.player_id, self.next_player_id, HAND_RESULTS, message["data"]
            )


    def handle_new_dealer(self, message):
        self.is_dealer = True
        if self.check_winner():
            return

        self.hands = [[] for _ in range(NUM_PLAYERS)]
        self.bets = [-1] * NUM_PLAYERS
        self.deck = []
        self.played_cards = [""] * NUM_PLAYERS  # Track played cards
        self.points = [0] * NUM_PLAYERS
        print(
                Fore.GREEN
                + "You are the new dealer"
                + Style.RESET_ALL
            )
        input(
                Fore.YELLOW
                + "Press ENTER to shuffle the cards after all players are online!..."
                + Style.RESET_ALL
            )
        self.create_deck()
        print(Fore.YELLOW + "Cards have been shuffled!..." + Style.RESET_ALL)
        self.deal_cards()
        self.ask_for_bets()

    def handle_player_won(self, message):
        winner = message["data"]
        self.update_display()
        print(Fore.GREEN + f"Player {winner} won!"  + Style.RESET_ALL)
        if not self.is_dealer:
            self.network.send(
                    self.player_id, self.next_player_id, PLAYER_WON, message["data"]
                )
        exit()

