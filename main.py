from dataclasses import dataclass
from enum import Enum
import random


# TODO
# 1. DONE Make all rules truly configurable
#    - With exception to re-split, surrender and insurance
# 2. Move classes to separate files
# 3. Add cut card
# 4. Add rules to config file
# 5. Add card counting config
# 6. Hook up into martingale simulator
# 7. Documentation and clean up
# 8. Make this user playable
# 9. Make a GUI for this
# 10. How much money do you lose with worse blackjack payouts?
# 11. How much of an edge does card counting give you?
# 12. How bad is it when players play randomly and you're card counting?
# 13. How bad is it when players play by the book and you're card counting?
# 14. How bad is it when players all card count and you're card counting?
#


class DealerStand(Enum):
    HIT_SOFT_SEVENTEEN = 1
    STAND_SOFT_SEVENTEEN = 2


class GameState(Enum):
    '''
    Enum which models the flow of the game.
    PLAYER AND DEALER ACTIONS ALTERNATE UNTIL CHECK GAME STATE SAYS ITS DONE.
    '''
    INITIAL_DEAL     = 1 # Dealer deals their card and everyone elses hand
    PLAYER_ACTION    = 2 # Dealer asks if each player wants to hit
    DEALER_ACTION    = 3 # Dealer turns card
    CHECK_GAME_STATE = 4 # Determines whether the hand is over
    NOT_PLAYING      = 5 # The default state


class PlayerAction(Enum):
    '''
    Enum which models a potential player action.
    '''
    INITIAL     = 1
    HIT         = 2
    STAND       = 3
    DOUBLE_DOWN = 4
    SPLIT       = 5


@dataclass
class Rules:
    ''' Class for modeling blackjack rules. '''
    num_decks:         int
    num_players:       int
    num_simulations:   int
    blackjack_payout:  float
    allow_double_down: bool
    allow_re_split:    bool
    allow_surrender:   bool
    allow_insurance:   bool
    dealer_stand:      DealerStand


class CardType(Enum):
    UNDEFINED = 0
    HEARTS    = 1
    DIAMONDS  = 2
    SPADES    = 3
    CLUBS     = 4


class CardValue(Enum):
    CUT   = 0
    ACE   = 1
    TWO   = 2
    THREE = 3
    FOUR  = 4
    FIVE  = 5
    SIX   = 6
    SEVEN = 7
    EIGHT = 8
    NINE  = 9
    TEN   = 10
    JACK  = 11
    QUEEN = 12
    KING  = 13


@dataclass
class Card:
    card_type:  CardType
    card_value: CardValue

    def __str__(self) -> str:
        return f'{self.card_value.name} OF {self.card_type.name}'

    def __eq__(self, value):
        return self.card_type == value.card_type and self.card_value == value.card_value

    def values(self) -> list:
        hard_value = self.card_value.value if self.card_value.value < 10 else 10
        soft_value = hard_value if self.card_value is not CardValue.ACE else 11
        return [ hard_value, soft_value ]


class Deck:
    def __init__(self, num_decks = 0):
        self.cards = []
        self.num_decks = num_decks
        for _ in range(self.num_decks):
            self.add_new_deck()
        self.shuffle()

    def cards(self) -> list:
        return self.cards

    def add_new_deck(self) -> None:
        self.cards.extend(self.deck_of_cards())

    def append(self, card : Card) -> None:
        self.cards.append(card)

    def shuffle(self) -> None:
        random.shuffle(self.cards)

    def reset(self) -> None:
        self.cards = []

    def draw_card(self) -> Card:
        if not self.cards:
            # TODO: Do proper cutting with the cut card
            self.cards = []
            for _ in range(self.num_decks):
                self.add_new_deck()
            self.shuffle()
            
        return self.cards.pop()

    @staticmethod
    def deck_of_cards() -> list:
        deck = []
        for type in CardType:
            for value in CardValue:
                if type is not CardType.UNDEFINED and value is not CardValue.CUT:
                    deck.append(Card(type, value))
        return deck


class Hand:
    def __init__(self) -> None:
        self.cards    = []
        self.bet_size = 100
        self.result   = False

    def __str__(self) -> str:
        res = ''
        for i, card in enumerate(self.cards):
            res += str(card)
            if i < len(self.cards) - 1:
                res += ', '
        return res

    def num_cards(self) -> int:
        return len(self.cards)

    def double_down(self) -> None:
        self.bet_size *= 2

    def add_card(self, card : Card) -> None:
        self.cards.append(card)

    def face_card(self) -> Card:
        return self.cards[0]

    def can_be_split(self) -> bool:
        if len(self.cards) != 2:
            return False
        return self.cards[0].card_value == self.cards[1].card_value

    def split_card(self) -> Card:
        if not self.can_be_split():
            return None
        return self.cards[0]

    def totals(self) -> list:
        totals = [0, 0]
        for card in self.cards:
            card_values = card.values()
            totals[0] += card_values[0]
            totals[1] += card_values[1]
        return totals

    def is_bust(self) -> bool:
        totals = self.totals()
        return totals[0] > 21 and totals[1] > 21

    def best_total(self) -> int:
        if self.is_bust():
            return 0
        totals = self.totals()
        max_total = max(totals[0], totals[1])
        min_total = min(totals[0], totals[1])
        return max_total if max_total <= 21 else min_total

    def set_result(self, result) -> None:
        self.result = result

    def result_string(self) -> str:
        return f'\033[42mWON {self.totals_string()}\033[0m' if self.result else f'\033[41mLOST {self.totals_string()}\033[0m'

    def totals_string(self) -> str:
        totals = self.totals()
        return f'H:{totals[0]} S:{totals[1]}'



class TheBook:
    '''
    Class Modelling a the blackjack book.
    '''
    def __init__(self, rules : Rules):
        self.rules = rules

        self.hard_book = {
            2 : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.HIT,
                CardValue.THREE : PlayerAction.HIT,
                CardValue.FOUR  : PlayerAction.HIT,
                CardValue.FIVE  : PlayerAction.HIT,
                CardValue.SIX   : PlayerAction.HIT,
                CardValue.SEVEN : PlayerAction.HIT,
                CardValue.EIGHT : PlayerAction.HIT,
                CardValue.NINE  : PlayerAction.HIT,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            3 : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.HIT,
                CardValue.THREE : PlayerAction.HIT,
                CardValue.FOUR  : PlayerAction.HIT,
                CardValue.FIVE  : PlayerAction.HIT,
                CardValue.SIX   : PlayerAction.HIT,
                CardValue.SEVEN : PlayerAction.HIT,
                CardValue.EIGHT : PlayerAction.HIT,
                CardValue.NINE  : PlayerAction.HIT,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            4 : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.HIT,
                CardValue.THREE : PlayerAction.HIT,
                CardValue.FOUR  : PlayerAction.HIT,
                CardValue.FIVE  : PlayerAction.HIT,
                CardValue.SIX   : PlayerAction.HIT,
                CardValue.SEVEN : PlayerAction.HIT,
                CardValue.EIGHT : PlayerAction.HIT,
                CardValue.NINE  : PlayerAction.HIT,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            5 : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.HIT,
                CardValue.THREE : PlayerAction.HIT,
                CardValue.FOUR  : PlayerAction.HIT,
                CardValue.FIVE  : PlayerAction.HIT,
                CardValue.SIX   : PlayerAction.HIT,
                CardValue.SEVEN : PlayerAction.HIT,
                CardValue.EIGHT : PlayerAction.HIT,
                CardValue.NINE  : PlayerAction.HIT,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            6 : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.HIT,
                CardValue.THREE : PlayerAction.HIT,
                CardValue.FOUR  : PlayerAction.HIT,
                CardValue.FIVE  : PlayerAction.HIT,
                CardValue.SIX   : PlayerAction.HIT,
                CardValue.SEVEN : PlayerAction.HIT,
                CardValue.EIGHT : PlayerAction.HIT,
                CardValue.NINE  : PlayerAction.HIT,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            7 : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.HIT,
                CardValue.THREE : PlayerAction.HIT,
                CardValue.FOUR  : PlayerAction.HIT,
                CardValue.FIVE  : PlayerAction.HIT,
                CardValue.SIX   : PlayerAction.HIT,
                CardValue.SEVEN : PlayerAction.HIT,
                CardValue.EIGHT : PlayerAction.HIT,
                CardValue.NINE  : PlayerAction.HIT,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            8 : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.HIT,
                CardValue.THREE : PlayerAction.HIT,
                CardValue.FOUR  : PlayerAction.HIT,
                CardValue.FIVE  : PlayerAction.HIT,
                CardValue.SIX   : PlayerAction.HIT,
                CardValue.SEVEN : PlayerAction.HIT,
                CardValue.EIGHT : PlayerAction.HIT,
                CardValue.NINE  : PlayerAction.HIT,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            9 : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.HIT,
                CardValue.THREE : PlayerAction.DOUBLE_DOWN,
                CardValue.FOUR  : PlayerAction.DOUBLE_DOWN,
                CardValue.FIVE  : PlayerAction.DOUBLE_DOWN,
                CardValue.SIX   : PlayerAction.DOUBLE_DOWN,
                CardValue.SEVEN : PlayerAction.HIT,
                CardValue.EIGHT : PlayerAction.HIT,
                CardValue.NINE  : PlayerAction.HIT,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            10 : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.DOUBLE_DOWN,
                CardValue.THREE : PlayerAction.DOUBLE_DOWN,
                CardValue.FOUR  : PlayerAction.DOUBLE_DOWN,
                CardValue.FIVE  : PlayerAction.DOUBLE_DOWN,
                CardValue.SIX   : PlayerAction.DOUBLE_DOWN,
                CardValue.SEVEN : PlayerAction.DOUBLE_DOWN,
                CardValue.EIGHT : PlayerAction.DOUBLE_DOWN,
                CardValue.NINE  : PlayerAction.DOUBLE_DOWN,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            11 : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.DOUBLE_DOWN,
                CardValue.THREE : PlayerAction.DOUBLE_DOWN,
                CardValue.FOUR  : PlayerAction.DOUBLE_DOWN,
                CardValue.FIVE  : PlayerAction.DOUBLE_DOWN,
                CardValue.SIX   : PlayerAction.DOUBLE_DOWN,
                CardValue.SEVEN : PlayerAction.DOUBLE_DOWN,
                CardValue.EIGHT : PlayerAction.DOUBLE_DOWN,
                CardValue.NINE  : PlayerAction.DOUBLE_DOWN,
                CardValue.TEN   : PlayerAction.DOUBLE_DOWN,
                CardValue.JACK  : PlayerAction.DOUBLE_DOWN,
                CardValue.QUEEN : PlayerAction.DOUBLE_DOWN,
                CardValue.KING  : PlayerAction.DOUBLE_DOWN
            },
            12 : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.HIT,
                CardValue.THREE : PlayerAction.HIT,
                CardValue.FOUR  : PlayerAction.STAND,
                CardValue.FIVE  : PlayerAction.STAND,
                CardValue.SIX   : PlayerAction.STAND,
                CardValue.SEVEN : PlayerAction.HIT,
                CardValue.EIGHT : PlayerAction.HIT,
                CardValue.NINE  : PlayerAction.HIT,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            13 : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.STAND,
                CardValue.THREE : PlayerAction.STAND,
                CardValue.FOUR  : PlayerAction.STAND,
                CardValue.FIVE  : PlayerAction.STAND,
                CardValue.SIX   : PlayerAction.STAND,
                CardValue.SEVEN : PlayerAction.HIT,
                CardValue.EIGHT : PlayerAction.HIT,
                CardValue.NINE  : PlayerAction.HIT,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            14 : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.STAND,
                CardValue.THREE : PlayerAction.STAND,
                CardValue.FOUR  : PlayerAction.STAND,
                CardValue.FIVE  : PlayerAction.STAND,
                CardValue.SIX   : PlayerAction.STAND,
                CardValue.SEVEN : PlayerAction.HIT,
                CardValue.EIGHT : PlayerAction.HIT,
                CardValue.NINE  : PlayerAction.HIT,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            15 : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.STAND,
                CardValue.THREE : PlayerAction.STAND,
                CardValue.FOUR  : PlayerAction.STAND,
                CardValue.FIVE  : PlayerAction.STAND,
                CardValue.SIX   : PlayerAction.STAND,
                CardValue.SEVEN : PlayerAction.HIT,
                CardValue.EIGHT : PlayerAction.HIT,
                CardValue.NINE  : PlayerAction.HIT,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            16 : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.STAND,
                CardValue.THREE : PlayerAction.STAND,
                CardValue.FOUR  : PlayerAction.STAND,
                CardValue.FIVE  : PlayerAction.STAND,
                CardValue.SIX   : PlayerAction.STAND,
                CardValue.SEVEN : PlayerAction.HIT,
                CardValue.EIGHT : PlayerAction.HIT,
                CardValue.NINE  : PlayerAction.HIT,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            17 : {
                CardValue.ACE   : PlayerAction.STAND,
                CardValue.TWO   : PlayerAction.STAND,
                CardValue.THREE : PlayerAction.STAND,
                CardValue.FOUR  : PlayerAction.STAND,
                CardValue.FIVE  : PlayerAction.STAND,
                CardValue.SIX   : PlayerAction.STAND,
                CardValue.SEVEN : PlayerAction.STAND,
                CardValue.EIGHT : PlayerAction.STAND,
                CardValue.NINE  : PlayerAction.STAND,
                CardValue.TEN   : PlayerAction.STAND,
                CardValue.JACK  : PlayerAction.STAND,
                CardValue.QUEEN : PlayerAction.STAND,
                CardValue.KING  : PlayerAction.STAND
            },
            18 : {
                CardValue.ACE   : PlayerAction.STAND,
                CardValue.TWO   : PlayerAction.STAND,
                CardValue.THREE : PlayerAction.STAND,
                CardValue.FOUR  : PlayerAction.STAND,
                CardValue.FIVE  : PlayerAction.STAND,
                CardValue.SIX   : PlayerAction.STAND,
                CardValue.SEVEN : PlayerAction.STAND,
                CardValue.EIGHT : PlayerAction.STAND,
                CardValue.NINE  : PlayerAction.STAND,
                CardValue.TEN   : PlayerAction.STAND,
                CardValue.JACK  : PlayerAction.STAND,
                CardValue.QUEEN : PlayerAction.STAND,
                CardValue.KING  : PlayerAction.STAND
            },
            19 : {
                CardValue.ACE   : PlayerAction.STAND,
                CardValue.TWO   : PlayerAction.STAND,
                CardValue.THREE : PlayerAction.STAND,
                CardValue.FOUR  : PlayerAction.STAND,
                CardValue.FIVE  : PlayerAction.STAND,
                CardValue.SIX   : PlayerAction.STAND,
                CardValue.SEVEN : PlayerAction.STAND,
                CardValue.EIGHT : PlayerAction.STAND,
                CardValue.NINE  : PlayerAction.STAND,
                CardValue.TEN   : PlayerAction.STAND,
                CardValue.JACK  : PlayerAction.STAND,
                CardValue.QUEEN : PlayerAction.STAND,
                CardValue.KING  : PlayerAction.STAND
            },
            20 : {
                CardValue.ACE   : PlayerAction.STAND,
                CardValue.TWO   : PlayerAction.STAND,
                CardValue.THREE : PlayerAction.STAND,
                CardValue.FOUR  : PlayerAction.STAND,
                CardValue.FIVE  : PlayerAction.STAND,
                CardValue.SIX   : PlayerAction.STAND,
                CardValue.SEVEN : PlayerAction.STAND,
                CardValue.EIGHT : PlayerAction.STAND,
                CardValue.NINE  : PlayerAction.STAND,
                CardValue.TEN   : PlayerAction.STAND,
                CardValue.JACK  : PlayerAction.STAND,
                CardValue.QUEEN : PlayerAction.STAND,
                CardValue.KING  : PlayerAction.STAND
            },
            21 : {
                CardValue.ACE   : PlayerAction.STAND,
                CardValue.TWO   : PlayerAction.STAND,
                CardValue.THREE : PlayerAction.STAND,
                CardValue.FOUR  : PlayerAction.STAND,
                CardValue.FIVE  : PlayerAction.STAND,
                CardValue.SIX   : PlayerAction.STAND,
                CardValue.SEVEN : PlayerAction.STAND,
                CardValue.EIGHT : PlayerAction.STAND,
                CardValue.NINE  : PlayerAction.STAND,
                CardValue.TEN   : PlayerAction.STAND,
                CardValue.JACK  : PlayerAction.STAND,
                CardValue.QUEEN : PlayerAction.STAND,
                CardValue.KING  : PlayerAction.STAND
            }
        }

        self.soft_book = {
            13 : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.HIT,
                CardValue.THREE : PlayerAction.HIT,
                CardValue.FOUR  : PlayerAction.HIT,
                CardValue.FIVE  : PlayerAction.DOUBLE_DOWN,
                CardValue.SIX   : PlayerAction.DOUBLE_DOWN,
                CardValue.SEVEN : PlayerAction.HIT,
                CardValue.EIGHT : PlayerAction.HIT,
                CardValue.NINE  : PlayerAction.HIT,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            14 : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.HIT,
                CardValue.THREE : PlayerAction.HIT,
                CardValue.FOUR  : PlayerAction.HIT,
                CardValue.FIVE  : PlayerAction.DOUBLE_DOWN,
                CardValue.SIX   : PlayerAction.DOUBLE_DOWN,
                CardValue.SEVEN : PlayerAction.HIT,
                CardValue.EIGHT : PlayerAction.HIT,
                CardValue.NINE  : PlayerAction.HIT,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            15 : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.HIT,
                CardValue.THREE : PlayerAction.HIT,
                CardValue.FOUR  : PlayerAction.DOUBLE_DOWN,
                CardValue.FIVE  : PlayerAction.DOUBLE_DOWN,
                CardValue.SIX   : PlayerAction.DOUBLE_DOWN,
                CardValue.SEVEN : PlayerAction.HIT,
                CardValue.EIGHT : PlayerAction.HIT,
                CardValue.NINE  : PlayerAction.HIT,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            16 : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.HIT,
                CardValue.THREE : PlayerAction.HIT,
                CardValue.FOUR  : PlayerAction.DOUBLE_DOWN,
                CardValue.FIVE  : PlayerAction.DOUBLE_DOWN,
                CardValue.SIX   : PlayerAction.DOUBLE_DOWN,
                CardValue.SEVEN : PlayerAction.HIT,
                CardValue.EIGHT : PlayerAction.HIT,
                CardValue.NINE  : PlayerAction.HIT,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            17 : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.HIT,
                CardValue.THREE : PlayerAction.DOUBLE_DOWN,
                CardValue.FOUR  : PlayerAction.DOUBLE_DOWN,
                CardValue.FIVE  : PlayerAction.DOUBLE_DOWN,
                CardValue.SIX   : PlayerAction.DOUBLE_DOWN,
                CardValue.SEVEN : PlayerAction.HIT,
                CardValue.EIGHT : PlayerAction.HIT,
                CardValue.NINE  : PlayerAction.HIT,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            18 : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.STAND,
                CardValue.THREE : PlayerAction.DOUBLE_DOWN,
                CardValue.FOUR  : PlayerAction.DOUBLE_DOWN,
                CardValue.FIVE  : PlayerAction.DOUBLE_DOWN,
                CardValue.SIX   : PlayerAction.DOUBLE_DOWN,
                CardValue.SEVEN : PlayerAction.STAND,
                CardValue.EIGHT : PlayerAction.STAND,
                CardValue.NINE  : PlayerAction.HIT,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            19 : {
                CardValue.ACE   : PlayerAction.STAND,
                CardValue.TWO   : PlayerAction.STAND,
                CardValue.THREE : PlayerAction.STAND,
                CardValue.FOUR  : PlayerAction.STAND,
                CardValue.FIVE  : PlayerAction.STAND,
                CardValue.SIX   : PlayerAction.STAND,
                CardValue.SEVEN : PlayerAction.STAND,
                CardValue.EIGHT : PlayerAction.STAND,
                CardValue.NINE  : PlayerAction.STAND,
                CardValue.TEN   : PlayerAction.STAND,
                CardValue.JACK  : PlayerAction.STAND,
                CardValue.QUEEN : PlayerAction.STAND,
                CardValue.KING  : PlayerAction.STAND
            }
        }

        self.split_book = {
            CardValue.ACE : {
                CardValue.ACE   : PlayerAction.SPLIT,
                CardValue.TWO   : PlayerAction.SPLIT,
                CardValue.THREE : PlayerAction.SPLIT,
                CardValue.FOUR  : PlayerAction.SPLIT,
                CardValue.FIVE  : PlayerAction.SPLIT,
                CardValue.SIX   : PlayerAction.SPLIT,
                CardValue.SEVEN : PlayerAction.SPLIT,
                CardValue.EIGHT : PlayerAction.SPLIT,
                CardValue.NINE  : PlayerAction.SPLIT,
                CardValue.TEN   : PlayerAction.SPLIT,
                CardValue.JACK  : PlayerAction.SPLIT,
                CardValue.QUEEN : PlayerAction.SPLIT,
                CardValue.KING  : PlayerAction.SPLIT
            },
            CardValue.TWO : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.SPLIT,
                CardValue.THREE : PlayerAction.SPLIT,
                CardValue.FOUR  : PlayerAction.SPLIT,
                CardValue.FIVE  : PlayerAction.SPLIT,
                CardValue.SIX   : PlayerAction.SPLIT,
                CardValue.SEVEN : PlayerAction.SPLIT,
                CardValue.EIGHT : PlayerAction.HIT,
                CardValue.NINE  : PlayerAction.HIT,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            CardValue.THREE : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.SPLIT,
                CardValue.THREE : PlayerAction.SPLIT,
                CardValue.FOUR  : PlayerAction.SPLIT,
                CardValue.FIVE  : PlayerAction.SPLIT,
                CardValue.SIX   : PlayerAction.SPLIT,
                CardValue.SEVEN : PlayerAction.SPLIT,
                CardValue.EIGHT : PlayerAction.HIT,
                CardValue.NINE  : PlayerAction.HIT,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            CardValue.FOUR : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.HIT,
                CardValue.THREE : PlayerAction.HIT,
                CardValue.FOUR  : PlayerAction.HIT,
                CardValue.FIVE  : PlayerAction.SPLIT,
                CardValue.SIX   : PlayerAction.SPLIT,
                CardValue.SEVEN : PlayerAction.HIT,
                CardValue.EIGHT : PlayerAction.HIT,
                CardValue.NINE  : PlayerAction.HIT,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            # FIVE IS A NEVER SPLIT
            CardValue.SIX : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.SPLIT,
                CardValue.THREE : PlayerAction.SPLIT,
                CardValue.FOUR  : PlayerAction.SPLIT,
                CardValue.FIVE  : PlayerAction.SPLIT,
                CardValue.SIX   : PlayerAction.SPLIT,
                CardValue.SEVEN : PlayerAction.HIT,
                CardValue.EIGHT : PlayerAction.HIT,
                CardValue.NINE  : PlayerAction.HIT,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            CardValue.SEVEN : {
                CardValue.ACE   : PlayerAction.HIT,
                CardValue.TWO   : PlayerAction.SPLIT,
                CardValue.THREE : PlayerAction.SPLIT,
                CardValue.FOUR  : PlayerAction.SPLIT,
                CardValue.FIVE  : PlayerAction.SPLIT,
                CardValue.SIX   : PlayerAction.SPLIT,
                CardValue.SEVEN : PlayerAction.SPLIT,
                CardValue.EIGHT : PlayerAction.HIT,
                CardValue.NINE  : PlayerAction.HIT,
                CardValue.TEN   : PlayerAction.HIT,
                CardValue.JACK  : PlayerAction.HIT,
                CardValue.QUEEN : PlayerAction.HIT,
                CardValue.KING  : PlayerAction.HIT
            },
            CardValue.EIGHT : {
                CardValue.ACE   : PlayerAction.SPLIT,
                CardValue.TWO   : PlayerAction.SPLIT,
                CardValue.THREE : PlayerAction.SPLIT,
                CardValue.FOUR  : PlayerAction.SPLIT,
                CardValue.FIVE  : PlayerAction.SPLIT,
                CardValue.SIX   : PlayerAction.SPLIT,
                CardValue.SEVEN : PlayerAction.SPLIT,
                CardValue.EIGHT : PlayerAction.SPLIT,
                CardValue.NINE  : PlayerAction.SPLIT,
                CardValue.TEN   : PlayerAction.SPLIT,
                CardValue.JACK  : PlayerAction.SPLIT,
                CardValue.QUEEN : PlayerAction.SPLIT,
                CardValue.KING  : PlayerAction.SPLIT
            },
            CardValue.NINE : {
                CardValue.ACE   : PlayerAction.STAND,
                CardValue.TWO   : PlayerAction.SPLIT,
                CardValue.THREE : PlayerAction.SPLIT,
                CardValue.FOUR  : PlayerAction.SPLIT,
                CardValue.FIVE  : PlayerAction.SPLIT,
                CardValue.SIX   : PlayerAction.SPLIT,
                CardValue.SEVEN : PlayerAction.SPLIT,
                CardValue.EIGHT : PlayerAction.SPLIT,
                CardValue.NINE  : PlayerAction.SPLIT,
                CardValue.TEN   : PlayerAction.STAND,
                CardValue.JACK  : PlayerAction.STAND,
                CardValue.QUEEN : PlayerAction.STAND,
                CardValue.KING  : PlayerAction.STAND
            }
            # TEN IS A NEVER SPLIT
        }

    def player_best_move(self, hand : Hand, face_card : Card, has_split : bool) -> PlayerAction:
        hard_value, soft_value = hand.totals()

        if hard_value <= 1:
            temp = 1

        hard_best_move  = self.hard_book[hard_value][face_card.card_value] if hard_value <= 21 else None
        soft_best_move  = self.hard_book[soft_value][face_card.card_value] if soft_value <= 21 else None
        split_best_move = None
        if not has_split and hand.can_be_split() and hand.split_card().card_value in self.split_book:
                split_best_move = self.split_book[hand.split_card().card_value][face_card.card_value]

        if split_best_move is not None:  return split_best_move
        elif soft_best_move is not None: return soft_best_move
        elif hard_best_move is not None: return hard_best_move
        assert False, 'SHOULD NEVER REACH HERE'
        return None

    def dealer_best_move(self, hand : Hand) -> PlayerAction:
        hard_value, soft_value = hand.totals()
        if self.rules.dealer_stand is DealerStand.HIT_SOFT_SEVENTEEN and hard_value < soft_value:
            return PlayerAction.STAND if soft_value > 17 else PlayerAction.HIT
        else:
            return PlayerAction.STAND if soft_value >= 17 else PlayerAction.HIT


class Player:
    '''
    Class Modelling a Black Jack Player.
    '''
    def __init__(self, rules : Rules) -> None:
        '''
        Constructor.
        '''
        self.rules     = rules
        self.book      = TheBook(self.rules)
        self.money     = 0
        self.reset()

        # Stats
        self.num_hands      = 0
        self.num_wins       = 0
        self.num_pushes     = 0
        self.num_blackjacks = 0

    def reset(self):
        '''
        Resets the player.
        '''
        self.hands     = [ Hand() ]
        self.bet_size  = 100
        self.has_split = False

    def add_card(self, card : Card) -> None:
        '''
        Adds a card to our hand.
        Method should only be called when no split has occurred.
        '''
        assert len(self.hands) == 1, f'Error: A split has occurred.: {len(self.hands)}'
        self.hands[0].add_card(card)

    def perform_actions(self, face_card : Card, shoe : Deck) -> None:
        '''
        Usually just does one perform_action call.
        However, if we split we have to play multiple hands.
        '''
        player_action = self.perform_action(self.hands[0], face_card, shoe)
        for hand in self.hands:
            while player_action is not PlayerAction.STAND:
                player_action = self.perform_action(hand, face_card, shoe)

    def perform_action(self, hand : Hand, face_card : Card, shoe : Deck) -> PlayerAction:
        '''
        Queries the blackjack book for the best move.
        Then performs that move.
        Only HIT, STAND, DOUBLE_DOWN, and SPLIT are supported.
        '''
        if hand.is_bust():
            return PlayerAction.STAND

        player_action = self.book.player_best_move(hand, face_card, self.has_split)

        match player_action:
            case PlayerAction.HIT:         return self.hit(hand, shoe)
            case PlayerAction.STAND:       return self.stand(hand, shoe)
            case PlayerAction.DOUBLE_DOWN: return self.double_down(hand, shoe)
            case PlayerAction.SPLIT:       return self.split(hand, shoe)
            case _:                        return player_action

        return player_action

    def hit(self, hand : Hand, shoe : Deck):
        '''
        Hits. Adds card to hand from shoe.
        '''
        hand.add_card(shoe.draw_card())

        return PlayerAction.HIT

    def stand(self, hand : Hand, shoe : Deck):
        '''
        Stands. Does nothing.
        '''
        return PlayerAction.STAND

    def double_down(self, hand : Hand, shoe : Deck):
        '''
        Doubles down.
        '''
        if self.rules.allow_double_down:
            hand.add_card(shoe.draw_card())
            hand.double_down()
            return PlayerAction.STAND
        else:
            return self.hit(hand, shoe)

    def split(self, hand : Hand, shoe : Deck):
        '''
        Splits the hand.
        '''
        self.has_split = True
        card = self.hands[0].split_card()
        self.hands.clear()
        for i in range(2):
            self.hands.append(Hand())
            self.hands[i].add_card(card)
            self.hands[i].add_card(shoe.draw_card())

        return PlayerAction.SPLIT

    def won_or_lost(self, dealer_total : int) -> None:
        '''
        If the player won, increment their money by the bet.
        If the player lost, decrement their money by the bet.
        '''
        global num_hands
        global num_hands_won

        for hand in self.hands:
            num_hands += 1
            self.num_hands += 1
            total = hand.best_total()
            if total == 0: # bust
                hand.set_result(False)
                self.money -= self.bet_size
            elif total == dealer_total:
                self.num_pushes += 1
                hand.set_result(False)
            elif total < dealer_total:
                hand.set_result(False)
                self.money -= self.bet_size
            elif total == 21 and hand.num_cards() == 2:
                self.num_blackjacks += 1
                num_hands_won += 1
                self.num_wins += 1
                hand.set_result(True)
                self.money += (self.rules.blackjack_payout * self.bet_size)
            elif total > dealer_total:
                num_hands_won += 1
                self.num_wins += 1
                hand.set_result(True)
                self.money += self.bet_size
            else:
                assert False, 'UH OH'

    def hand_string(self) -> str:
        res = ''
        for i, hand in enumerate(self.hands):
            res += str(hand)
            res += f' {hand.result_string()} '
            if i < len(self.hands) - 1:
                res += 'and '
        return res

    def player_win_percentage_str(self) -> str:
        return f'Won {round((self.num_wins / self.num_hands) * 100, 2)}%. Push {round((self.num_pushes / self.num_hands) * 100, 2)}%. BJ {round((self.num_blackjacks / self.num_hands) * 100, 2)}%'


class Dealer:
    '''
    Class Modelling a Black Jack Dealer.
    '''
    # TODO: Reset the shoe and discard pile if we've reached the cut card
    #
    def __init__(self, rules : Rules) -> None:
        '''
        Constructor
        '''
        self.rules        = rules
        self.shoe         = Deck(self.rules.num_decks)
        self.discard_pile = Deck()
        self.book         = TheBook(self.rules)
        self.players      = [ Player(self.rules) for _ in range(self.rules.num_players) ]
        self.reset_table()

    def reset_table(self) -> None:
        '''
        Resets the table for a hand.
        '''
        self.hand    = Hand()
        for player in self.players:
            player.reset()

    def perform_action(self, game_state : GameState) -> GameState:
        '''
        Factory method for performing a blackjack action. 
        '''
        match game_state:
            case game_state.INITIAL_DEAL:     return self.initial_deal()
            case game_state.PLAYER_ACTION:    return self.player_action()
            case game_state.DEALER_ACTION:    return self.dealer_action()
            case game_state.CHECK_GAME_STATE: return self.check_game_state()
            case _:                           return GameState.NOT_PLAYING

        return GameState.NOT_PLAYING

    def initial_deal(self) -> GameState:
        '''
        Performs the initial hand deal.
        '''
        for _ in range(2):
            self.hand.add_card(self.shoe.draw_card())
            for player in self.players:
                player.add_card(self.shoe.draw_card())

        return GameState.PLAYER_ACTION

    def player_action(self) -> GameState:
        '''
        Performs the player action for each player.
        '''
        for player in self.players:
            player.perform_actions(self.hand.face_card(), self.shoe)

        return GameState.DEALER_ACTION

    def dealer_action(self) -> GameState:
        '''
        Performs the dealer action.
        '''
        dealer_action = PlayerAction.HIT
        while dealer_action is not PlayerAction.STAND:
            dealer_action = self.book.dealer_best_move(self.hand)
            if dealer_action is PlayerAction.HIT:
                self.hand.add_card(self.shoe.draw_card())

        return GameState.CHECK_GAME_STATE

    def check_game_state(self) -> GameState:
        '''
        Checks the game state and sends back to player action if more can be done.
        Otherwise, ends the hand.
        '''
        dealer_total = self.hand.best_total()

        for player in self.players:
            player.won_or_lost(dealer_total)

        # Log our results
        print(f'Dealer Hand: {str(self.hand)} {self.hand.totals_string()}')
        for i, player in enumerate(self.players):
            print(f'Player {i + 1} Hand: {player.hand_string()}')
        print()

        return GameState.NOT_PLAYING

    def print_results(self):
        '''
        Prints the player results.
        '''
        for i, player in enumerate(self.players):
            print(f'Player {i + 1} has ${player.money}. {player.player_win_percentage_str()}')


class Table:
    '''
    Class Modelling a Black Jack Table.
    '''
    def __init__(self, rules : Rules) -> None:
        '''
        Constructor
        '''
        self.dealer          = Dealer(rules)
        self.num_simulations = rules.num_simulations
        self.game_state      = GameState.INITIAL_DEAL

    def run_simulations(self) -> None:
        '''
        Entry point to hands of blackjack
        '''
        count = 0
        for _ in range(self.num_simulations):
            count += 1
            print(f'Playing hand #{count}')
            self.play_hand()
            self.dealer.reset_table()
            self.game_state = GameState.INITIAL_DEAL
        print(f'Ran {count} BlackJack Simulations.')
        print('The results are: ')
        self.dealer.print_results()
        print(f'Number of hands played: {num_hands}')
        print(f'Number of hands won: {num_hands_won}')
        print(f'Win Percentage: %{round((num_hands_won / num_hands) * 100, 2)}')


    def play_hand(self) -> None:
        '''
        Main hand loop.
        '''
        while self.game_state is not GameState.NOT_PLAYING:
            self.game_state = self.dealer.perform_action(self.game_state)


def play_blackjack():
    '''
    The entry point of black jack!

    1 Shoe.
    6 decks in a shoe.
    1 cut card, anywhere where there is about 1 -> 1.5 decks left.
    Play blackjack until shoe is empty.
    1 Discard pile.

    When Shoe we reach the cut card, we add the discard pile back to the shoe and reshuffle.

    State:
    Table
    Shoe List
    Discard List
    Dealer
    Player List

    Dealer Actions:
    Shuffle Shoe
    Deal Cards
    Ask for bets
    Determine who wins and loses

    Player Actions:
    Bet
    Hit
    Stay
    Split

    Rules:
    Will play at a table with 6 players.
    Dealer will stand on a soft 17
    Black Jack 3/2 Payoff
    Doubling down (Only allowed a one card hit)
    Re-split Aces up to 3 hands
    Re-split Pairs up to 3 hands
    No surrender
    No insurance

    Design:
    Table
    -> Table Rules
    -> Shoe
    -> Discard Pile
    -> Dealer
    -> Player List

    Dealer
    -> Dealer Actions

    Player
    -> Player Actions
    -> Count
    '''
    # Initialize the rules
    #
    NUM_DECKS         = 6
    NUM_PLAYERS       = 6
    NUM_SIMULATIONS   = 10_000
    BLACKJACK_PAYOUT  = 1.5 # 3/2
    ALLOW_DOUBLE_DOWN = True
    ALLOW_RE_SPLIT    = False # This is a nice to have but we won't implement this yet
    ALLOW_SURRENDER   = False # This is a nice to have but we won't implement this yet
    ALLOW_INSURANCE   = False # You should never have insurance
    DEALER_STAND      = DealerStand.STAND_SOFT_SEVENTEEN
    RULES = Rules(
        NUM_DECKS,
        NUM_PLAYERS,
        NUM_SIMULATIONS,
        BLACKJACK_PAYOUT,
        ALLOW_DOUBLE_DOWN,
        ALLOW_RE_SPLIT,
        ALLOW_SURRENDER,
        ALLOW_INSURANCE,
        DEALER_STAND)

    # Initialize the table and play blackjack.
    #
    table = Table(RULES)
    table.run_simulations()


if __name__ == '__main__':
    '''
    Main Method
    '''
    # import sys
    # sys.stdout = open('output.txt', 'w+')

    num_hands     = 0
    num_hands_won = 0

    play_blackjack()