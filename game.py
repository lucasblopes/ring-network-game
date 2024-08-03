import random
from settings import NUM_PLAYERS, NUM_CARDS, LIVES, SUIT_EMOJIS
from settings import clear_screen

SUITS = ["Hearts", "Diamonds", "Clubs", "Spades"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

# Actions
# obs1.: carteador sempre eh o primeiro a realizar as acoes
# obs1.: so passa o bastao depois do final de uma rodada
NEW_DEALER = 1  # self.id|next_player.id|1 (1 msg)
DEAL_CARDS = 2  # dealer.id|next_player.d|2|cards,cards,cards... (3 msg)
ASK_BETS = 3  # dealer.id|next_player.id|3|bet,bet,bet,bet (msg da a volta coletando a bet de cada um, que vai modificando a msg) (1 msg)
SHOW_BETS = 4  # dealer.id|next_player.id|4|bet,bet,bet,bet (msg para cada jogador atualizar a tela de bets) (1msg)
ASK_CARD = 5  # dealer.id|next_player.id|5|card,card,card,card
RESULTS = 6  # dealer.id|next_player.id|7|life,life,life,life
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

    def create_deck(self):
        self.deck = [{"suit": suit, "rank": rank} for suit in SUITS for rank in RANKS]
        random.shuffle(self.deck)

    def deal_cards(self):
        input("Press ENTER to deal cards...")
        for i in range(NUM_PLAYERS):
            self.hands[i] = [self.deck.pop() for _ in range(NUM_CARDS)]
        print(f"Player {self.player_id} dealt cards.")
        self.print_hand()

        for i in range(NUM_PLAYERS):
            if i != self.player_id:
                data = ",".join(
                    [f"{card['rank']}-{card['suit']}" for card in self.hands[i]]
                )
                self.network.send(self.player_id, i, DEAL_CARDS, data)

    def print_hand(self):
        print(f"Player {self.player_id} hand:")
        for index, card in enumerate(self.hands[self.player_id]):
            print(f"{index}: {card['rank']} {SUIT_EMOJIS[card['suit']]}")

    def print_scoreboard(self):
        print("\nScoreboard:")
        for i in range(NUM_PLAYERS):
            print(f"Player {i}: {self.lives[i]} lives")
        print()

    def update_scoreboard(self):
        lives_data = ",".join([str(life) for life in self.lives])
        self.network.send(
            self.player_id,
            self.next_player_id,
            UPDATE_SCOREBOARD,
            lives_data,
        )

    def start(self):
        print("Player", self.player_id, "joined the game!")
        if self.is_dealer:
            input("Press ENTER to shuffle the cards after all players are online!...")
            self.create_deck()
            print("Cards have been shuffled!...")
            clear_screen()
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
                self.print_scoreboard()

    def ask_for_bets(self):
        if self.is_dealer:
            bet = self.get_valid_bet()
            self.bets[self.player_id] = bet
            bet_data = f"{self.player_id}-{bet}"
            self.network.send(self.player_id, self.next_player_id, ASK_BETS, bet_data)

    def place_bet(self, player_id, bet):
        self.bets[player_id] = bet
        if all(
            bet != -1 for bet in self.bets
        ):  # Check if all players have placed their bets
            self.show_bets()

    def show_bets(self):
        if self.is_dealer:
            bets_data = ",".join([f"{i}-{self.bets[i]}" for i in range(NUM_PLAYERS)])
            self.network.send(self.player_id, self.next_player_id, SHOW_BETS, bets_data)

    def ask_for_cards(self):
        if self.is_dealer:
            print("Starting the game...")
            self.print_hand()
            card_index = self.get_valid_card_index()
            card = self.hands[self.player_id][card_index]
            print(
                f"Player {self.player_id} chose card {card['rank']} {SUIT_EMOJIS[card['suit']]}"
            )
            card_data = f"{self.player_id}-{self.hands[self.player_id][card_index]['rank']}-{self.hands[self.player_id][card_index]['suit']}"
            self.hands[self.player_id].pop(card_index)
            self.network.send(self.player_id, self.next_player_id, ASK_CARD, card_data)

    def get_valid_card_index(self):
        while True:
            try:
                card_index = int(
                    input(f"Player {self.player_id}, choose a card by index: ")
                )
                if 0 <= card_index < len(self.hands[self.player_id]):
                    return card_index
                else:
                    print("Invalid index. Please choose a valid card index.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def handle_round_end(self, card_data):
        print("Round ended. Cards played:", card_data)
        self.compute_round_results(card_data)
        self.start_next_round()

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

    def get_valid_bet(self):
        while True:
            try:
                bet = int(input(f"Player {self.player_id}, enter your bet: "))
                if 0 <= bet < len(self.hands[self.player_id]):
                    return bet
                else:
                    print("Invalid bet. Please choose a valid bet.")
            except ValueError:
                print("Invalid input. Please enter a number.")

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

    def handle_show_bets(self, message):
        print(f"Bets: {message['data']}")
        if self.is_dealer:
            self.ask_for_cards()
        else:
            self.network.send(
                message["source"], self.next_player_id, SHOW_BETS, message["data"]
            )

    def handle_ask_card(self, message):
        played_cards = message["data"].split(",")
        print(played_cards)
        if not any(
            self.player_id == int(card.split("-")[0]) for card in played_cards if card
        ):
            print("Your hand:")
            self.print_hand()
            card_index = self.get_valid_card_index()
            print("Card choosed by Player")
            card = self.hands[self.player_id].pop(card_index)
            played_cards.append(f"{self.player_id}-{card['rank']}-{card['suit']}")

        if self.is_dealer:
            print("All players have played their cards.")
            self.handle_round_end(",".join(played_cards))
        else:
            self.network.send(
                self.player_id, self.next_player_id, ASK_CARD, ",".join(played_cards)
            )

    # implementar
    def handle_new_dealer(self, message):
        pass

    # implementar
    def handle_update_scoreboard(self, message):
        pass
