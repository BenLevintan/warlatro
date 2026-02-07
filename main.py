# main.py
import arcade
import arcade.gl
import random
import enum
from collections import Counter

# Import our new modules
import config
import sprites
import ui_elements

class GameState(enum.Enum):
    DRAWING = 1
    DECIDING = 2
    SHOPPING = 3
    GAME_OVER = 4

class WarGame(arcade.Window):
    def __init__(self):
        super().__init__(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, config.SCREEN_TITLE)
        
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
        self.hands_max = config.BASE_HANDS_TO_PLAY
        self.discards_left = config.MAX_DISCARDS
        self.target_score = config.BASE_TARGET_SCORE
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
        
        self.hovered_joker = None 
        self.mouse_x = 0
        self.mouse_y = 0
        
        self.background_color = config.COLOR_BG

        # --- SHADER SETUP ---
        self.shader_time = 0.0 
        
        self.program = self.ctx.program(
            vertex_shader=config.VERTEX_SHADER,
            fragment_shader=config.FRAGMENT_SHADER,
        )
        self.quad_fs = arcade.gl.geometry.quad_2d_fs()
        
        self.screen_texture = self.ctx.texture((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.fbo = self.ctx.framebuffer(color_attachments=[self.screen_texture])

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
        self.hands_max = config.BASE_HANDS_TO_PLAY + bonus_hands
        
        self.hands_played = 0
        self.score_total = 0
        self.discards_left = config.MAX_DISCARDS
        self.message = f"Level {self.round_level} Start!"
        self.hand_details = []
        
        self.btn_action = ui_elements.TextButton(config.SCREEN_WIDTH/2, 280, 240, 50, "TAKE CARD", config.COLOR_BTN_ACTION)
        self.btn_score = ui_elements.TextButton(config.SCREEN_WIDTH - 150, 150, 200, 60, "SCORE HAND", config.COLOR_BTN_SCORE)
        self.btn_sell = ui_elements.TextButton(0, 0, 100, 40, "SELL", config.COLOR_BTN_SELL) 
        self.btn_sell.visible = False
        
        self.create_deck()
        self.draw_new_card()

    def create_deck(self):
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        self.deck = []
        for suit in suits:
            for rank in ranks:
                card = sprites.Card(suit, rank, config.CARD_SCALE)
                self.deck.append(card)
        random.shuffle(self.deck)

    def draw_new_card(self):
        if len(self.deck) > 0:
            card = self.deck.pop()
            card.center_x = config.SCREEN_WIDTH + 150
            card.center_y = config.DRAWN_CARD_Y
            card.target_x = config.DRAWN_CARD_X
            card.target_y = config.DRAWN_CARD_Y
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
        available_keys = [k for k in config.JOKER_DATA.keys() if k not in owned_keys]
        choices = random.sample(available_keys, min(2, len(available_keys)))
        
        start_x = config.SCREEN_WIDTH / 2 - 150
        for i, key in enumerate(choices):
            joker = sprites.Joker(key, config.JOKER_SCALE)
            joker.center_x = start_x + (i * 300)
            joker.center_y = config.SCREEN_HEIGHT / 2 + 100 
            self.shop_list.append(joker)
            
            btn = ui_elements.TextButton(joker.center_x, joker.center_y - 170, 120, 40, f"BUY ${joker.cost}", config.COLOR_BTN_SHOP)
            if self.coins < joker.cost:
                btn.active = False
                btn.text = f"  Need ${joker.cost}"
            self.shop_buttons.append(btn)

        self.btn_next_round = ui_elements.TextButton(config.SCREEN_WIDTH - 150, 80, 200, 60, "NEXT LEVEL >", config.COLOR_GREEN)

    def buy_joker(self, index):
        if index >= len(self.shop_list): return
        
        target_joker = self.shop_list[index]
        if self.coins >= target_joker.cost:
            if len(self.joker_list) < config.MAX_JOKERS:
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
        start_x = config.SCREEN_WIDTH - 100
        for i, joker in enumerate(self.joker_list):
            joker.center_x = start_x - (i * (config.JOKER_WIDTH + 50))
            joker.center_y = config.SCREEN_HEIGHT - 250
            joker.scale = 0.25

    # --- SCORING LOGIC ---
    def calculate_score(self):
        if not self.hand_list: return 0, 1, []

        base_sum = sum(c.value for c in self.hand_list)
        
        additive_mult = 1
        final_multiplier = 1
        
        bonus_points = 0
        breakdown = []

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

        sorted_ranks = sorted([c.value for c in self.hand_list])
        unique_ranks = sorted(list(set(sorted_ranks)))
        has_3_straight = False
        consecutive = 0
        
        for i in range(len(unique_ranks) - 1):
            if unique_ranks[i+1] == unique_ranks[i] + 1:
                consecutive += 1
                if consecutive >= 2: 
                    has_3_straight = True
            else:
                consecutive = 0
        
        if {14, 2, 3}.issubset(set(unique_ranks)):
            has_3_straight = True

        for joker in self.joker_list:
            if joker.key == "pear_up" and (has_pair or has_trip): 
                additive_mult += 8
                breakdown.append("PearUp(+8)")
            
            if joker.key == "triple_treat" and has_trip:
                additive_mult += 12
                breakdown.append("TripTreat(+12)")
                
            if joker.key == "inflation" and len(self.hand_list) <= config.MAX_HAND_SIZE - 1: # 4 cards
                additive_mult += 12
                breakdown.append("Inflation(+12)")
        
        for joker in self.joker_list:
            if joker.key == "multi_python" and has_3_straight:
                final_multiplier *= 2
                breakdown.append("Python(x2)")

        total_mult = additive_mult * final_multiplier
        total_base = base_sum + bonus_points
        
        return total_base, total_mult, breakdown
    
    def on_update(self, delta_time):
        self.shader_time += delta_time
        self.card_list.update()

    def draw_game_contents(self):
        # 1. Backgrounds
        arcade.draw_rect_filled(arcade.XYWH(config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT - 40, config.SCREEN_WIDTH, 80), config.COLOR_UI_BG)
        
        # 2. Stats Text
        arcade.draw_text(f"Lvl: {self.round_level}", 20, config.SCREEN_HEIGHT - 50, config.COLOR_WHITE, 16)
        arcade.draw_text(f"Target: {self.score_total} / {self.target_score}", 150, config.SCREEN_HEIGHT - 50, config.COLOR_WHITE, 20, bold=True)
        arcade.draw_text(f"Coins: ${self.coins}", config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT - 50, config.COLOR_GOLD, 20, bold=True, anchor_x="center")

        if self.state != GameState.GAME_OVER:
             arcade.draw_text(f"Hands: {self.hands_max - self.hands_played}", config.SCREEN_WIDTH - 250, config.SCREEN_HEIGHT - 35, config.COLOR_WHITE, 16, anchor_x="right")
             color_disc = config.COLOR_BTN_ACTION if self.discards_left > 0 else config.COLOR_RED
             arcade.draw_text(f"Discards: {self.discards_left}", config.SCREEN_WIDTH - 250, config.SCREEN_HEIGHT - 65, color_disc, 16, anchor_x="right")

        # 3. Game Area
        if self.state == GameState.SHOPPING:
            arcade.draw_text(self.message, config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT - 150, config.COLOR_WHITE, 20, anchor_x="center", align="center")
            
            ui_elements.draw_shadows(self.shop_list)
            self.shop_list.draw()
            
            for btn in self.shop_buttons:
                btn.draw()
            if self.btn_next_round: self.btn_next_round.draw()

        else: # Playing
            arcade.draw_text(self.message, config.SCREEN_WIDTH/2, 380, config.COLOR_WHITE, 16, anchor_x="center", align="center")
            
            start_y = 200
            for i, line in enumerate(self.hand_details):
                arcade.draw_text(line, config.SCREEN_WIDTH - 150, start_y + (i * 20), config.COLOR_GOLD, 14, anchor_x="center", bold=True)

            start_x = (config.SCREEN_WIDTH - (config.MAX_HAND_SIZE * (config.CARD_WIDTH + 20))) / 2 + config.CARD_WIDTH / 2
            for i in range(config.MAX_HAND_SIZE):
                slot_x = start_x + i * (config.CARD_WIDTH + 20)
                rect = arcade.XYWH(slot_x, config.HAND_Y, config.CARD_WIDTH, config.CARD_HEIGHT)
                arcade.draw_rect_outline(rect, config.COLOR_GREEN, 2)
            
            if self.state != GameState.GAME_OVER:
                new_rect = arcade.XYWH(config.DRAWN_CARD_X, config.DRAWN_CARD_Y, config.CARD_WIDTH + 10, config.CARD_HEIGHT + 10)
                arcade.draw_rect_outline(new_rect, config.COLOR_WHITE, 2)
                arcade.draw_text("NEW CARD", config.DRAWN_CARD_X, config.DRAWN_CARD_Y + 110, config.COLOR_WHITE, 12, anchor_x="center")

            ui_elements.draw_shadows(self.card_list)
            self.card_list.draw()
            
            for card in self.hand_list:
                if card.is_selected:
                    h_rect = arcade.XYWH(card.center_x, card.center_y, config.CARD_WIDTH + 12, config.CARD_HEIGHT + 12)
                    arcade.draw_rect_outline(h_rect, config.COLOR_RED, 4)

            self.update_game_buttons() 
            if self.btn_action: self.btn_action.draw()
            if self.btn_score: self.btn_score.draw()

            if self.state == GameState.GAME_OVER:
                overlay = arcade.XYWH(config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT/2, 500, 300)
                arcade.draw_rect_filled(overlay, config.COLOR_BLACK)
                arcade.draw_rect_outline(overlay, config.COLOR_WHITE, 4)
                arcade.draw_text("GAME OVER", config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT/2 + 50, config.COLOR_RED, 40, anchor_x="center", bold=True)
                arcade.draw_text(f"Final Score: {self.score_total}", config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT/2, config.COLOR_WHITE, 20, anchor_x="center")
                arcade.draw_text("Click to Restart", config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT/2 - 60, (150, 150, 150), 16, anchor_x="center")

        ui_elements.draw_shadows(self.joker_list)
        self.joker_list.draw()
        
        for joker in self.joker_list:
            if joker.is_selected:
                r = arcade.XYWH(joker.center_x, joker.center_y, config.JOKER_WIDTH * 0.35, 120 * 0.35) 
                arcade.draw_rect_outline(r, config.COLOR_BTN_SELL, 2)
                self.btn_sell.center_x = joker.center_x
                self.btn_sell.center_y = joker.center_y - 60
                self.btn_sell.text = f"SELL ${joker.sell_price}"
                self.btn_sell.visible = True
                self.btn_sell.draw()

        ui_elements.draw_tooltip(self.hovered_joker, self.mouse_x, self.mouse_y)

    def on_draw(self):
        self.fbo.use()
        self.fbo.clear(color=config.COLOR_BG)
        self.draw_game_contents()
        
        self.use()
        self.clear()
        
        self.program['texture0'] = 0 
        self.program['pixel_size'] = 1.5 
        self.program['screen_size'] = (float(config.SCREEN_WIDTH), float(config.SCREEN_HEIGHT))
        self.program['time'] = self.shader_time
        
        self.screen_texture.use(0)
        self.quad_fs.render(self.program)

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
            self.btn_action.base_color = config.COLOR_BTN_ACTION
            if len(self.hand_list) >= config.MAX_HAND_SIZE:
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

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y
        
        self.hovered_joker = None
        check_lists = [self.joker_list]
        if self.state == GameState.SHOPPING:
            check_lists.append(self.shop_list)
            
        for sprite_list in check_lists:
            hit = arcade.get_sprites_at_point((x, y), sprite_list)
            if hit:
                self.hovered_joker = hit[0]
                break

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
            self.target_score = config.BASE_TARGET_SCORE
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

        for card in to_remove:
            self.hand_list.remove(card) 
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
        
        for card in list(self.hand_list): 
            self.hand_list.remove(card)
            card.target_y = config.SCREEN_HEIGHT + 300 
            card.should_despawn = True
            
        self.hand_list.clear()
        
        if self.score_total >= self.target_score:
            self.enter_shop()
            return

        self.hands_played += 1
        if self.hands_played >= self.hands_max:
            self.state = GameState.GAME_OVER
        else:
            self.message = f"Scored {final_score}! ({base} x {multi})"

    def reposition_hand(self):
        start_x = (config.SCREEN_WIDTH - (len(self.hand_list) * (config.CARD_WIDTH + 20))) / 2 + config.CARD_WIDTH / 2
        for i, card in enumerate(self.hand_list):
            card.target_x = start_x + i * (config.CARD_WIDTH + 20)
            card.target_y = config.HAND_Y
            card.is_selected = False

def main():
    window = WarGame()
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()