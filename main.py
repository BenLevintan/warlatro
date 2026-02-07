import arcade
import random
import enum
from collections import Counter

# --- Constants ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 900
SCREEN_TITLE = "Warlatro: Roguelike War"

# Card sizing
CARD_SCALE = 0.8
CARD_WIDTH = 140 * CARD_SCALE
CARD_HEIGHT = 190 * CARD_SCALE

# Joker Sizing
JOKER_SCALE = 0.3
JOKER_WIDTH = 250 * JOKER_SCALE

# UI Positioning
HAND_Y = 150
DRAWN_CARD_X = SCREEN_WIDTH / 2
DRAWN_CARD_Y = 480

# Animation Physics (Spring Effect)
STIFFNESS = 0.1
DAMPING = 0.75

# Game Logic
MAX_HAND_SIZE = 5
BASE_HANDS_TO_PLAY = 3
MAX_DISCARDS = 5
BASE_TARGET_SCORE = 300
MAX_JOKERS = 3

# --- Colors ---
COLOR_BG = (59, 122, 87)
COLOR_UI_BG = (26, 36, 33)
COLOR_BTN_DEFAULT = (128, 128, 128)
COLOR_BTN_HOVER = (119, 136, 153)
COLOR_BTN_ACTION = (30, 144, 255)
COLOR_BTN_SCORE = (255, 165, 0)
COLOR_BTN_SHOP = (75, 0, 130)
COLOR_BTN_SELL = (220, 20, 60)
COLOR_RED = (255, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GREEN = (0, 100, 0)
COLOR_GOLD = (255, 215, 0)

# --- Joker Definitions ---
JOKER_DATA = {
    "pear_up": {
        "name": "Pear-Up", "cost": 4, "desc": "+8 Mult if Pair",
        "file": "assets/jokers/pear_up.jpg"
    },
    "helping_hand": {
        "name": "Helping Hand", "cost": 5, "desc": "+1 Hand per Round",
        "file": "assets/jokers/helping_hand.jpg"
    },
    "triple_treat": {
        "name": "Triple Treat", "cost": 4, "desc": "+12 Mult if 3-of-a-Kind",
        "file": "assets/jokers/triple_treat.jpg"
    },
    "multi_python": {
        "name": "Multi Python", "cost": 7, "desc": "x2 Mult if 3-card Straight",
        "file": "assets/jokers/multi_python.jpg"
    },
    "inflation": {
        "name": "Inflation", "cost": 6, "desc": "+12 Mult if Hand <= 4 cards",
        "file": "assets/jokers/inflation.jpg"
    }
}


class GameState(enum.Enum):
    DRAWING = 1
    DECIDING = 2
    SHOPPING = 3
    GAME_OVER = 4


class TextButton:
    def __init__(self, cx, cy, width, height, text, color=COLOR_BTN_DEFAULT, text_color=COLOR_WHITE):
        self.center_x = cx
        self.center_y = cy
        self.width = width
        self.height = height
        self.text = "   " + text
        self.base_color = color
        self.highlight_color = COLOR_BTN_HOVER
        self.text_color = text_color
        self.is_hovered = False
        self.visible = True
        self.active = True

    def draw(self):
        if not self.visible: return

        if not self.active:
            draw_color = (100, 100, 100)
        elif self.is_hovered:
            draw_color = self.highlight_color
        else:
            draw_color = self.base_color

        rect = arcade.XYWH(self.center_x, self.center_y, self.width, self.height)
        arcade.draw_rect_filled(rect, draw_color)
        arcade.draw_rect_outline(rect, COLOR_WHITE, 2)

        arcade.draw_text(
            self.text, self.center_x, self.center_y, self.text_color,
            font_size=14, bold=True, anchor_x="center", anchor_y="center",
            multiline=True, width=self.width
        )

    def check_mouse_hover(self, x, y):
        if not self.visible: return
        half_w, half_h = self.width / 2, self.height / 2
        self.is_hovered = (self.center_x - half_w < x < self.center_x + half_w) and \
                          (self.center_y - half_h < y < self.center_y + half_h)

    def is_clicked(self, x, y):
        return self.visible and self.active and self.is_hovered


class Joker(arcade.Sprite):
    def __init__(self, key, scale=1.0):
        data = JOKER_DATA[key]
        super().__init__(data['file'], scale)
        self.key = key
        self.name = data['name']
        self.cost = data['cost']
        self.desc = data['desc']
        self.sell_price = self.cost // 2
        self.is_selected = False


class Card(arcade.Sprite):
    def __init__(self, suit, rank, scale=1):
        self.suit = suit
        self.rank = rank

        # Calculate Value
        if rank in ['J', 'Q', 'K', 'A']:
            if rank == 'J':
                self.value = 11
            elif rank == 'Q':
                self.value = 12
            elif rank == 'K':
                self.value = 13
            elif rank == 'A':
                self.value = 14
        else:
            self.value = int(rank)

        # Determine Color
        if suit in ['Hearts', 'Diamonds']:
            self.color_type = 'Red'
        else:
            self.color_type = 'Black'

        image_file = f":resources:images/cards/card{suit}{rank}.png"
        super().__init__(image_file, scale)
        self.is_selected = False

        # --- Physics Properties ---
        self.target_x = 0
        self.target_y = 0
        self.vel_x = 0
        self.vel_y = 0
        self.should_despawn = False

    def update(self, delta_time: float = 1 / 60):
        """ Arcade calls this automatically every frame when list.update() is used """

        # 1. Spring Physics Calculation
        dx = self.target_x - self.center_x
        dy = self.target_y - self.center_y

        force_x = dx * STIFFNESS
        force_y = dy * STIFFNESS

        self.vel_x = (self.vel_x + force_x) * DAMPING
        self.vel_y = (self.vel_y + force_y) * DAMPING

        self.center_x += self.vel_x
        self.center_y += self.vel_y

        # 2. Despawn Logic (fly off screen)
        if self.should_despawn:
            if (self.center_y < -200 or self.center_y > SCREEN_HEIGHT + 200):
                self.remove_from_sprite_lists()


class WarGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)

        # Sprite Lists
        self.card_list = None
        self.hand_list = None
        self.joker_list = None
        self.shop_list = None
        self.drawn_card = None

        # Game State
        self.state = GameState.DRAWING
        self.deck = []
        self.score_total = 0
        self.hands_played = 0
        self.hands_max = BASE_HANDS_TO_PLAY
        self.discards_left = MAX_DISCARDS
        self.target_score = BASE_TARGET_SCORE
        self.round_level = 1
        self.coins = 5

        self.message = ""
        self.hand_details = []

        # Buttons
        self.btn_action = None
        self.btn_score = None
        self.btn_next_round = None
        self.btn_sell = None
        self.shop_buttons = []

        self.background_color = COLOR_BG

    def setup(self):
        self.card_list = arcade.SpriteList()
        self.hand_list = arcade.SpriteList()
        self.joker_list = arcade.SpriteList()
        self.shop_list = arcade.SpriteList()
        self.drawn_card = None

        self.start_new_round()

    def start_new_round(self):
        self.state = GameState.DRAWING
        self.card_list.clear()
        self.hand_list.clear()
        self.shop_list.clear()
        self.shop_buttons = []

        bonus_hands = sum(1 for j in self.joker_list if j.key == "helping_hand")
        self.hands_max = BASE_HANDS_TO_PLAY + bonus_hands

        self.hands_played = 0
        self.score_total = 0
        self.discards_left = MAX_DISCARDS
        self.message = f"Level {self.round_level} Start!"
        self.hand_details = []

        self.btn_action = TextButton(SCREEN_WIDTH / 2, 280, 240, 50, "TAKE CARD", COLOR_BTN_ACTION)
        self.btn_score = TextButton(SCREEN_WIDTH - 150, 150, 200, 60, "SCORE HAND", COLOR_BTN_SCORE)
        self.btn_sell = TextButton(0, 0, 100, 40, "SELL", COLOR_BTN_SELL)
        self.btn_sell.visible = False

        self.create_deck()
        self.draw_new_card()

    def create_deck(self):
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        self.deck = []
        for suit in suits:
            for rank in ranks:
                card = Card(suit, rank, CARD_SCALE)
                self.deck.append(card)
        random.shuffle(self.deck)

    def draw_new_card(self):
        if len(self.deck) > 0:
            card = self.deck.pop()

            # ANIMATION: Start off-screen right
            card.center_x = SCREEN_WIDTH + 150
            card.center_y = DRAWN_CARD_Y
            # Target
            card.target_x = DRAWN_CARD_X
            card.target_y = DRAWN_CARD_Y

            self.drawn_card = card
            self.card_list.append(card)
            self.state = GameState.DECIDING
        else:
            self.message = "Deck empty!"

    # --- SHOP SYSTEM ---
    def enter_shop(self):
        self.state = GameState.SHOPPING
        self.message = "SHOP PHASE\nBuy Jokers to help you!"

        hands_left = max(0, self.hands_max - self.hands_played)
        reward = (hands_left * 2) + (self.discards_left * 1)
        self.coins += reward
        self.message = f"Round Cleared!\nEarned ${reward} for unused resources."

        self.shop_list.clear()
        self.shop_buttons = []

        owned_keys = [j.key for j in self.joker_list]
        available_keys = [k for k in JOKER_DATA.keys() if k not in owned_keys]
        choices = random.sample(available_keys, min(2, len(available_keys)))

        start_x = SCREEN_WIDTH / 2 - 150
        for i, key in enumerate(choices):
            joker = Joker(key, JOKER_SCALE)
            joker.center_x = start_x + (i * 300)
            joker.center_y = SCREEN_HEIGHT / 2 + 100
            self.shop_list.append(joker)

            btn = TextButton(joker.center_x, joker.center_y - 170, 120, 40, f"BUY ${joker.cost}", COLOR_BTN_SHOP)
            if self.coins < joker.cost:
                btn.active = False
                btn.text = f"  Need ${joker.cost}"
            self.shop_buttons.append(btn)

        self.btn_next_round = TextButton(SCREEN_WIDTH - 150, 80, 200, 60, "NEXT LEVEL >", COLOR_GREEN)

    def buy_joker(self, index):
        if index >= len(self.shop_list): return

        target_joker = self.shop_list[index]
        if self.coins >= target_joker.cost:
            if len(self.joker_list) < MAX_JOKERS:
                self.coins -= target_joker.cost
                target_joker.remove_from_sprite_lists()
                self.joker_list.append(target_joker)
                self.reposition_jokers()
                self.shop_buttons.pop(index)
                self.enter_shop_refresh()
            else:
                self.message = "Inventory Full! (Max 3)"

    def enter_shop_refresh(self):
        for i, joker in enumerate(self.shop_list):
            if i < len(self.shop_buttons):
                btn = self.shop_buttons[i]
                if self.coins < joker.cost:
                    btn.active = False
                    btn.text = f"Need ${joker.cost}"
                else:
                    btn.active = True
                    btn.text = f"BUY ${joker.cost}"

    def sell_joker(self):
        to_sell = [j for j in self.joker_list if j.is_selected]
        for joker in to_sell:
            self.coins += joker.sell_price
            joker.remove_from_sprite_lists()
        self.reposition_jokers()
        self.btn_sell.visible = False

    def reposition_jokers(self):
        start_x = SCREEN_WIDTH - 100
        for i, joker in enumerate(self.joker_list):
            joker.center_x = start_x - (i * (JOKER_WIDTH + 20))
            joker.center_y = SCREEN_HEIGHT - 250
            joker.scale = 0.25

    # --- SCORING LOGIC ---
    def calculate_score(self):
        if not self.hand_list: return 0, 1, []

        base_sum = sum(c.value for c in self.hand_list)

        additive_mult = 1
        final_multiplier = 1

        bonus_points = 0
        breakdown = []

        # 1. Base Poker Logic
        ranks = [c.rank for c in self.hand_list]
        rank_counts = Counter(ranks).values()

        has_pair = False
        has_trip = False

        if 4 in rank_counts:
            additive_mult += 8
            breakdown.append("Quad(+8)")
        elif 3 in rank_counts:
            additive_mult += 3
            breakdown.append("Trip(+3)")
            has_trip = True

        pair_count = list(rank_counts).count(2)
        if pair_count > 0:
            bonus = pair_count * 2
            additive_mult += bonus
            breakdown.append(f"{pair_count} Pair(+{bonus})")
            has_pair = True

        suits = [c.suit for c in self.hand_list]
        if 5 in Counter(suits).values():
            additive_mult += 3
            breakdown.append("Flush(+3)")

        colors = [c.color_type for c in self.hand_list]
        if 5 in Counter(colors).values():
            additive_mult += 2
            breakdown.append("Color(+2)")

        # 2. Joker Logic
        sorted_ranks = sorted([c.value for c in self.hand_list])
        unique_ranks = sorted(list(set(sorted_ranks)))
        has_3_straight = False
        consecutive = 0

        # Check standard straight
        for i in range(len(unique_ranks) - 1):
            if unique_ranks[i + 1] == unique_ranks[i] + 1:
                consecutive += 1
                if consecutive >= 2:
                    has_3_straight = True
            else:
                consecutive = 0

        # FIXED: Check special Low Ace Straight (A, 2, 3) where A=14, 2=2, 3=3
        if {14, 2, 3}.issubset(set(unique_ranks)):
            has_3_straight = True

        # Apply Jokers (Additive First)
        for joker in self.joker_list:
            if joker.key == "pear_up" and (has_pair or has_trip):
                additive_mult += 8
                breakdown.append("PearUp(+8)")

            if joker.key == "triple_treat" and has_trip:
                additive_mult += 12
                breakdown.append("TripTreat(+12)")

            if joker.key == "inflation" and len(self.hand_list) <= 4:
                additive_mult += 12
                breakdown.append("Inflation(+12)")

        # Apply Jokers (Multiplicative Last)
        for joker in self.joker_list:
            if joker.key == "multi_python" and has_3_straight:
                final_multiplier *= 2
                breakdown.append("Python(x2)")

        # Final Calculation
        total_mult = additive_mult * final_multiplier
        total_base = base_sum + bonus_points

        return total_base, total_mult, breakdown

    # --- UPDATE LOOP ---
    def on_update(self, delta_time):
        self.card_list.update()

    # --- DRAWING ---
    def on_draw(self):
        self.clear()

        # -- Global UI --
        arcade.draw_rect_filled(arcade.XYWH(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 80), COLOR_UI_BG)
        arcade.draw_text(f"Lvl: {self.round_level}", 20, SCREEN_HEIGHT - 50, COLOR_WHITE, 16)
        arcade.draw_text(f"Target: {self.score_total} / {self.target_score}", 150, SCREEN_HEIGHT - 50, COLOR_WHITE, 20,
                         bold=True)
        arcade.draw_text(f"Coins: ${self.coins}", SCREEN_WIDTH / 2, SCREEN_HEIGHT - 50, COLOR_GOLD, 20, bold=True,
                         anchor_x="center")

        if self.state != GameState.GAME_OVER:
            arcade.draw_text(f"Hands: {self.hands_max - self.hands_played}", SCREEN_WIDTH - 250, SCREEN_HEIGHT - 35,
                             COLOR_WHITE, 16, anchor_x="right")
            color_disc = COLOR_BTN_ACTION if self.discards_left > 0 else COLOR_RED
            arcade.draw_text(f"Discards: {self.discards_left}", SCREEN_WIDTH - 250, SCREEN_HEIGHT - 65, color_disc, 16,
                             anchor_x="right")

        if self.state == GameState.SHOPPING:
            arcade.draw_text(self.message, SCREEN_WIDTH / 2, SCREEN_HEIGHT - 150, COLOR_WHITE, 20, anchor_x="center",
                             align="center")
            self.shop_list.draw()

            for joker in self.shop_list:
                arcade.draw_text(
                    joker.desc,
                    joker.center_x,
                    joker.center_y - 120,
                    COLOR_GOLD,
                    12,
                    anchor_x="center",
                    bold=True
                )

            for btn in self.shop_buttons:
                btn.draw()
            if self.btn_next_round: self.btn_next_round.draw()

        else:
            arcade.draw_text(self.message, SCREEN_WIDTH / 2, 380, COLOR_WHITE, 16, anchor_x="center", align="center")

            # Draw Breakdown Vertically
            start_y = 200
            for i, line in enumerate(self.hand_details):
                arcade.draw_text(line, SCREEN_WIDTH - 150, start_y + (i * 20), COLOR_GOLD, 14, anchor_x="center",
                                 bold=True)

            start_x = (SCREEN_WIDTH - (MAX_HAND_SIZE * (CARD_WIDTH + 20))) / 2 + CARD_WIDTH / 2
            for i in range(MAX_HAND_SIZE):
                slot_x = start_x + i * (CARD_WIDTH + 20)
                rect = arcade.XYWH(slot_x, HAND_Y, CARD_WIDTH, CARD_HEIGHT)
                arcade.draw_rect_outline(rect, COLOR_GREEN, 2)

            if self.state != GameState.GAME_OVER:
                new_rect = arcade.XYWH(DRAWN_CARD_X, DRAWN_CARD_Y, CARD_WIDTH + 10, CARD_HEIGHT + 10)
                arcade.draw_rect_outline(new_rect, COLOR_WHITE, 2)
                arcade.draw_text("NEW CARD", DRAWN_CARD_X, DRAWN_CARD_Y + 110, COLOR_WHITE, 12, anchor_x="center")

            self.card_list.draw()

            for card in self.hand_list:
                if card.is_selected:
                    # FIX: Center the highlight rect on the card's actual position.
                    h_rect = arcade.XYWH(card.center_x, card.center_y, CARD_WIDTH + 12, CARD_HEIGHT + 12)
                    arcade.draw_rect_outline(h_rect, COLOR_RED, 4)

            self.update_game_buttons()
            if self.btn_action: self.btn_action.draw()
            if self.btn_score: self.btn_score.draw()

            if self.state == GameState.GAME_OVER:
                overlay = arcade.XYWH(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, 500, 300)
                arcade.draw_rect_filled(overlay, COLOR_BLACK)
                arcade.draw_rect_outline(overlay, COLOR_WHITE, 4)
                arcade.draw_text("GAME OVER", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50, COLOR_RED, 40,
                                 anchor_x="center", bold=True)
                arcade.draw_text(f"Final Score: {self.score_total}", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, COLOR_WHITE,
                                 20, anchor_x="center")
                arcade.draw_text("Click to Restart", SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 60, (150, 150, 150), 16,
                                 anchor_x="center")

        self.joker_list.draw()
        for joker in self.joker_list:
            if joker.is_selected:
                r = arcade.XYWH(joker.center_x, joker.center_y, JOKER_WIDTH * 0.35, 120 * 0.35)
                arcade.draw_rect_outline(r, COLOR_BTN_SELL, 2)
                self.btn_sell.center_x = joker.center_x
                self.btn_sell.center_y = joker.center_y - 60
                self.btn_sell.text = f"SELL ${joker.sell_price}"
                self.btn_sell.visible = True
                self.btn_sell.draw()

    # --- UPDATE BUTTONS ---
    def update_game_buttons(self):
        if self.state == GameState.GAME_OVER:
            self.btn_action.visible = False
            self.btn_score.visible = False
            return

        self.btn_action.visible = True
        self.btn_score.visible = True

        num_selected = len([c for c in self.hand_list if c.is_selected])
        if num_selected > 0:
            self.btn_action.text = f"DISCARD ({num_selected}) & TAKE"
            self.btn_action.base_color = (220, 20, 60)
            self.btn_action.active = True
        else:
            self.btn_action.text = "TAKE CARD"
            self.btn_action.base_color = COLOR_BTN_ACTION
            if len(self.hand_list) >= MAX_HAND_SIZE:
                self.btn_action.active = False
                self.btn_action.text = "HAND FULL"
            else:
                self.btn_action.active = True

        if len(self.hand_list) > 0:
            s, m, desc = self.calculate_score()
            total = s * m
            self.btn_score.text = f"PLAY HAND\n{s} x {m} = {total}"
            self.hand_details = desc
            self.btn_score.active = True
        else:
            self.btn_score.text = "PLAY HAND"
            self.hand_details = []
            self.btn_score.active = False

    # --- INPUT HANDLING ---
    def on_mouse_motion(self, x, y, dx, dy):
        if self.state == GameState.SHOPPING:
            for btn in self.shop_buttons: btn.check_mouse_hover(x, y)
            if self.btn_next_round: self.btn_next_round.check_mouse_hover(x, y)
        else:
            if self.btn_action: self.btn_action.check_mouse_hover(x, y)
            if self.btn_score: self.btn_score.check_mouse_hover(x, y)

        if self.btn_sell.visible: self.btn_sell.check_mouse_hover(x, y)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.btn_sell.visible and self.btn_sell.is_clicked(x, y):
            self.sell_joker()
            return

        clicked_jokers = arcade.get_sprites_at_point((x, y), self.joker_list)
        if clicked_jokers:
            for j in self.joker_list: j.is_selected = False
            clicked_jokers[0].is_selected = True
            self.btn_sell.visible = True
            return
        else:
            for j in self.joker_list: j.is_selected = False
            self.btn_sell.visible = False

        if self.state == GameState.SHOPPING:
            for i, btn in enumerate(self.shop_buttons):
                if btn.is_clicked(x, y):
                    self.buy_joker(i)
                    return
            if self.btn_next_round and self.btn_next_round.is_clicked(x, y):
                self.round_level += 1
                self.target_score = int(self.target_score * 1.5)
                self.start_new_round()
                return

        elif self.state == GameState.GAME_OVER:
            self.round_level = 1
            self.target_score = BASE_TARGET_SCORE
            self.coins = 5
            self.joker_list.clear()
            self.setup()
            return

        elif self.state in [GameState.DECIDING, GameState.DRAWING]:
            if self.btn_action and self.btn_action.is_clicked(x, y):
                self.process_swap()
                return
            if self.btn_score and self.btn_score.is_clicked(x, y):
                self.score_hand()
                return

            if self.state == GameState.DECIDING and self.discards_left > 0:
                cards_clicked = arcade.get_sprites_at_point((x, y), self.hand_list)
                for card in cards_clicked:
                    card.is_selected = not card.is_selected

    def process_swap(self):
        to_remove = [c for c in self.hand_list if c.is_selected]
        if len(to_remove) > 0:
            if self.discards_left > 0:
                self.discards_left -= 1
            else:
                return

                # ANIMATION: Discard (fly down)
        for card in to_remove:
            self.hand_list.remove(card)
            # Note: card stays in self.card_list to render during anim
            card.target_y = -300
            card.should_despawn = True

        if self.drawn_card:
            self.hand_list.append(self.drawn_card)
            self.drawn_card = None
            self.reposition_hand()
            self.draw_new_card()

    def score_hand(self):
        base, multi, _ = self.calculate_score()
        final_score = base * multi
        self.score_total += final_score

        # ANIMATION: Played Cards (fly up)
        for card in list(self.hand_list):
            self.hand_list.remove(card)
            card.target_y = SCREEN_HEIGHT + 300
            card.should_despawn = True

        # self.hand_list is effectively empty here

        if self.score_total >= self.target_score:
            self.enter_shop()
            return

        self.hands_played += 1
        if self.hands_played >= self.hands_max:
            self.state = GameState.GAME_OVER
        else:
            self.message = f"Scored {final_score}! ({base} x {multi})"

    def reposition_hand(self):
        start_x = (SCREEN_WIDTH - (len(self.hand_list) * (CARD_WIDTH + 20))) / 2 + CARD_WIDTH / 2
        for i, card in enumerate(self.hand_list):
            card.target_x = start_x + i * (CARD_WIDTH + 20)
            card.target_y = HAND_Y
            card.is_selected = False


def main():
    window = WarGame()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()