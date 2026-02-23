import arcade
import arcade.gl
import enum
import warnings

warnings.filterwarnings("ignore") 

import config
import sprites
import ui_elements
import systems
import scoring

class GameState(enum.Enum):
    DRAWING = 1
    DECIDING = 2
    SHOPPING = 3
    PACK_OPENING = 4 
    GAME_OVER = 5

class WarGame(arcade.Window):
    def __init__(self):
        super().__init__(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, config.SCREEN_TITLE)
        
        self.deck_manager = None
        self.shop_manager = systems.ShopManager()
        self.audio_manager = systems.AudioManager() 

        self.card_list = arcade.SpriteList()
        self.hand_list = arcade.SpriteList()
        self.joker_list = arcade.SpriteList()
        self.shop_list = arcade.SpriteList()
        self.pack_card_list = arcade.SpriteList()
        self.animating_cards = arcade.SpriteList() # NEW: Keeps tracking cards after shop is closed
        self.drawn_card = None
        
        self.state = GameState.DRAWING
        self.score_total = 0
        self.hands_played = 0
        self.hands_max = config.BASE_HANDS_TO_PLAY
        self.discards_left = config.MAX_DISCARDS
        self.target_score = config.BASE_TARGET_SCORE
        self.round_level = 1
        self.coins = 5 
        self.run_discards = 0 
        
        self.message = ""
        self.hand_details = [] 
        
        self.btn_action = None 
        self.btn_score = None
        self.btn_next_round = None
        self.btn_sell = None
        self.shop_buttons = []
        
        self.btn_pack_skip = None
        self.btn_pack_mods = [] 
        self.pack_modifiers_offered = [] 
        
        self.hovered_joker = None 
        self.mouse_x = 0
        self.mouse_y = 0
        
        self.background_color = config.COLOR_BG

        self.shader_time = 0.0 
        self.program = self.ctx.program(vertex_shader=config.VERTEX_SHADER, fragment_shader=config.FRAGMENT_SHADER)
        self.quad_fs = arcade.gl.geometry.quad_2d_fs()
        self.screen_texture = self.ctx.texture((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.fbo = self.ctx.framebuffer(color_attachments=[self.screen_texture])

    def setup(self):
        self.score_total = 0
        self.round_level = 1
        self.target_score = config.BASE_TARGET_SCORE
        self.coins = 99995
        self.run_discards = 0
        
        self.joker_list.clear()
        self.animating_cards.clear()
        self.deck_manager = systems.DeckManager()
        
        self.audio_manager.start_bg_music() 
        
        self.start_new_round()

    def start_new_round(self):
        self.state = GameState.DRAWING
        self.card_list.clear()
        self.hand_list.clear()
        self.shop_list.clear()
        self.pack_card_list.clear()
        self.shop_buttons = []
        
        self.audio_manager.exit_store() 
        
        bonus_hands = sum(1 for j in self.joker_list if j.key == "helping_hand")
        bonus_discards = sum(1 for j in self.joker_list if j.key == "mulligan")
        
        self.hands_max = config.BASE_HANDS_TO_PLAY + bonus_hands
        self.discards_left = config.MAX_DISCARDS + bonus_discards
        
        self.hands_played = 0
        self.score_total = 0
        self.message = "" 
        self.hand_details = []
        
        self.deck_manager.start_round(self.card_list)

        self.btn_action = ui_elements.TextButton(config.SCREEN_WIDTH/2, 280, 240, 50, "TAKE CARD", config.COLOR_BTN_ACTION)
        self.btn_score = ui_elements.TextButton(config.SCREEN_WIDTH - 150, 150, 200, 60, "SCORE HAND", config.COLOR_BTN_SCORE)
        self.btn_sell = ui_elements.TextButton(0, 0, 100, 40, "SELL", config.COLOR_BTN_SELL) 
        self.btn_sell.visible = False
        
        self.draw_new_card()

    def draw_new_card(self):
        card = self.deck_manager.draw_card(self.card_list)
        
        if card:
            self.audio_manager.play_card_sound()
            
            start_x = config.SCREEN_WIDTH + 150
            start_y = config.DRAWN_CARD_Y
            card._phys_x = start_x
            card._phys_y = start_y
            card.center_x = start_x
            card.center_y = start_y
            card.target_x = config.DRAWN_CARD_X
            card.target_y = config.DRAWN_CARD_Y
            
            self.drawn_card = card
            self.state = GameState.DECIDING
        else:
            self.message = "DECK EMPTY!"

    def enter_shop(self):
        self.state = GameState.SHOPPING
        self.message = "SHOP PHASE"
        
        self.audio_manager.enter_store()
        
        hands_left = max(0, self.hands_max - self.hands_played)
        reward = (hands_left * 2) + (self.discards_left * 1)
        self.coins += reward
        
        bonus_discards = sum(1 for j in self.joker_list if j.key == "mulligan")
        start_discards = config.MAX_DISCARDS + bonus_discards
        
        nr_bonus = 0
        if self.discards_left == start_discards:
            nr_count = sum(1 for j in self.joker_list if j.key == "national_reserve")
            if nr_count > 0:
                nr_bonus = nr_count * 3
                self.coins += nr_bonus

        self.message = f"Round Cleared!\nEarned ${reward}."
        if nr_bonus > 0:
            self.message += f"\n(Reserve Bonus +${nr_bonus})"

        self.shop_manager.generate_shop(self.shop_list, self.shop_buttons, self.joker_list)
        
        self.btn_next_round = ui_elements.TextButton(config.SCREEN_WIDTH - 150, 80, 200, 60, "NEXT LEVEL >", config.COLOR_GREEN)
        self.update_shop_buttons()

    def update_shop_buttons(self):
        for i, item in enumerate(self.shop_list):
            if i < len(self.shop_buttons):
                btn = self.shop_buttons[i]
                if self.coins < item.cost:
                    btn.active = False
                    btn.text = f"Need ${item.cost}"
                else:
                    btn.active = True
                    btn.text = f"BUY ${item.cost}"

    def buy_shop_item(self, index):
        if index >= len(self.shop_list): return
        item = self.shop_list[index]
        
        if self.coins >= item.cost:
            if isinstance(item, sprites.Joker):
                if len(self.joker_list) < config.MAX_JOKERS:
                    self.coins -= item.cost
                    item.remove_from_sprite_lists()
                    self.joker_list.append(item)
                    self.reposition_jokers() 
                    self.shop_buttons.pop(index)
                    self.update_shop_buttons()
                    
                    self.audio_manager.play_buy_joker_fx() # NEW SOUND
                else:
                    self.message = "Inventory Full!"
            
            elif isinstance(item, sprites.Pack):
                self.coins -= item.cost
                item.remove_from_sprite_lists() 
                self.shop_buttons.pop(index)
                self.start_pack_opening()

    def start_pack_opening(self):
        self.state = GameState.PACK_OPENING
        self.message = "Select Cards then Choose Modifier"
        self.pack_card_list.clear()
        self.btn_pack_mods = []
        
        self.audio_manager.play_mod_fx() # NEW SOUND: When cards are pulled
        
        chosen_cards = self.shop_manager.get_pack_cards(self.deck_manager.master_deck)
        
        start_x = config.SCREEN_WIDTH / 2 - 250
        start_y = config.SCREEN_HEIGHT / 2 + 100
        for i, card in enumerate(chosen_cards):
            self.pack_card_list.append(card)
            card.visible = True
            card.is_selected = False
            
            row = i // 4
            col = i % 4
            tx = start_x + (col * (config.CARD_WIDTH + 20))
            ty = start_y - (row * (config.CARD_HEIGHT + 20))
            
            card._phys_x = config.SCREEN_WIDTH + 100 
            card._phys_y = ty
            card.target_x = tx
            card.target_y = ty

        self.pack_modifiers_offered = self.shop_manager.get_pack_modifiers()
        
        bx = config.SCREEN_WIDTH / 2 - 100
        by = 150
        for i, mod_key in enumerate(self.pack_modifiers_offered):
            data = config.MODIFIER_DATA[mod_key]
            btn = ui_elements.TextButton(bx + (i * 200), by, 180, 60, data['name'], data['color'])
            self.btn_pack_mods.append(btn)
            
        self.btn_pack_skip = ui_elements.TextButton(config.SCREEN_WIDTH - 100, 50, 100, 40, "SKIP", config.COLOR_BTN_DEFAULT)

    def apply_pack_modifier(self, mod_index):
        selected = [c for c in self.pack_card_list if c.is_selected]
        if not selected:
            self.message = "Select cards first!"
            return
            
        mod_key = self.pack_modifiers_offered[mod_index]
        self.audio_manager.play_mod_fx() # NEW SOUND: When applied
        
        for card in selected:
            card.modifier = mod_key
            card.is_selected = False
            
            # --- NEW ANIMATION LOGIC ---
            if mod_key == "destroy":
                card.is_spasming = True
            else:
                # Tell it to fly up and off screen
                card.target_y = config.SCREEN_HEIGHT + 400
                card.should_despawn = True
            
            # Move card out of the static UI list into our dynamic animation list
            self.animating_cards.append(card)
            
        self.state = GameState.SHOPPING
        self.pack_card_list.clear() # Clears remaining unselected cards immediately
        self.message = "Applied!"

    def score_hand(self):
        self.audio_manager.play_hand_fx()
        
        cards_in_deck = len(self.deck_manager.draw_pile)
        
        base, multi, desc, coin_bonus = scoring.calculate_hand_score(
            self.hand_list, self.joker_list, self.run_discards, cards_in_deck
        )
        final_score = base * multi
        self.score_total += final_score
        
        if coin_bonus > 0:
            self.coins += coin_bonus
        
        for card in list(self.hand_list): 
            self.hand_list.remove(card)
            self.deck_manager.discard_pile.append(card) 
            card.target_y = config.SCREEN_HEIGHT + 300 
            card.should_despawn = True
            
        self.hand_list.clear()
        
        if self.score_total >= self.target_score:
            self.enter_shop()
            return

        self.hands_played += 1
        if self.hands_played >= self.hands_max:
            self.state = GameState.GAME_OVER
            self.audio_manager.enter_game_over() 
        else:
            self.message = f"Scored {final_score}! ({base} x {multi})"
            if coin_bonus > 0:
                self.message += f" Earned ${coin_bonus}!"

    def process_swap(self):
        to_remove = [c for c in self.hand_list if c.is_selected]
        if len(to_remove) > 0:
            if self.discards_left > 0:
                self.discards_left -= 1
            else:
                return 
        
        self.run_discards += len(to_remove)

        for card in to_remove:
            self.hand_list.remove(card)
            self.deck_manager.discard_pile.append(card)
            card.target_y = -300
            card.should_despawn = True 
        
        if self.drawn_card:
            self.hand_list.append(self.drawn_card)
            self.drawn_card = None
            self.reposition_hand()
            self.draw_new_card()

    def on_update(self, delta_time):
        self.shader_time += delta_time
        
        self.audio_manager.update(delta_time)
        
        self.card_list.update()
        self.joker_list.update()
        self.shop_list.update()
        self.animating_cards.update() # NEW: Keeps updating modified cards
        if self.state == GameState.PACK_OPENING:
            self.pack_card_list.update()
        
        for card in self.hand_list:
            card.visible = True

    def draw_game_contents(self):
        arcade.draw_rect_filled(arcade.XYWH(config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT - 40, config.SCREEN_WIDTH, 80), config.COLOR_UI_BG)
        
        arcade.draw_text(f"Lvl: {self.round_level}", 20, config.SCREEN_HEIGHT - 50, config.COLOR_WHITE, 16)
        arcade.draw_text(f"Target: {self.score_total} / {self.target_score}", 150, config.SCREEN_HEIGHT - 50, config.COLOR_WHITE, 20, bold=True)
        arcade.draw_text(f"Coins: ${self.coins}", config.SCREEN_WIDTH / 2, config.SCREEN_HEIGHT - 50, config.COLOR_GOLD, 20, bold=True, anchor_x="center")

        if self.state != GameState.GAME_OVER:
             arcade.draw_text(f"Hands: {self.hands_max - self.hands_played}", config.SCREEN_WIDTH - 250, config.SCREEN_HEIGHT - 35, config.COLOR_WHITE, 16, anchor_x="right")
             color_disc = config.COLOR_BTN_ACTION if self.discards_left > 0 else config.COLOR_RED
             arcade.draw_text(f"Discards: {self.discards_left}", config.SCREEN_WIDTH - 250, config.SCREEN_HEIGHT - 65, color_disc, 16, anchor_x="right")

        if self.state == GameState.SHOPPING:
            arcade.draw_text(self.message, config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT - 150, config.COLOR_WHITE, 20, anchor_x="center", align="center")
            ui_elements.draw_shadows(self.shop_list)
            self.shop_list.draw()
            for btn in self.shop_buttons: btn.draw()
            if self.btn_next_round: self.btn_next_round.draw()

        elif self.state == GameState.PACK_OPENING:
            arcade.draw_text(self.message, config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT - 80, config.COLOR_WHITE, 20, anchor_x="center")
            ui_elements.draw_shadows(self.pack_card_list)
            self.pack_card_list.draw()
            for card in self.pack_card_list:
                card.draw_modifier()
                if card.is_selected:
                    arcade.draw_rect_outline(arcade.XYWH(card.center_x, card.center_y, config.CARD_WIDTH+10, config.CARD_HEIGHT+10), config.COLOR_GREEN, 4)
            for btn in self.btn_pack_mods: btn.draw()
            self.btn_pack_skip.draw()

        elif self.state == GameState.GAME_OVER:
            overlay = arcade.XYWH(config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT/2, 500, 300)
            arcade.draw_rect_filled(overlay, config.COLOR_BLACK)
            arcade.draw_rect_outline(overlay, config.COLOR_WHITE, 4)
            arcade.draw_text("GAME OVER", config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT/2 + 50, config.COLOR_RED, 40, anchor_x="center", bold=True)
            arcade.draw_text(f"Final Score: {self.score_total}", config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT/2, config.COLOR_WHITE, 20, anchor_x="center")
            arcade.draw_text("Click to Restart", config.SCREEN_WIDTH/2, config.SCREEN_HEIGHT/2 - 60, (150, 150, 150), 16, anchor_x="center")

        else: 
            if self.message:
                arcade.draw_text(self.message, config.SCREEN_WIDTH/2, 380, config.COLOR_WHITE, 16, anchor_x="center", align="center")
            
            cur_deck, total_deck = self.deck_manager.get_deck_counts()
            arcade.draw_text(f"Deck: {cur_deck} / {total_deck}", config.DRAWN_CARD_X, config.DRAWN_CARD_Y - 130, config.COLOR_WHITE, 12, anchor_x="center", bold=True)

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
            
            for card in self.card_list:
                card.draw_modifier()

            for card in self.hand_list:
                if card.is_selected:
                    h_rect = arcade.XYWH(card.center_x, card.center_y, config.CARD_WIDTH + 12, config.CARD_HEIGHT + 12)
                    arcade.draw_rect_outline(h_rect, config.COLOR_RED, 4)

            self.update_game_buttons() 
            if self.btn_action: self.btn_action.draw()
            if self.btn_score: self.btn_score.draw()

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
        
        # --- NEW: Draw Animating Pack Cards ON TOP ---
        ui_elements.draw_shadows(self.animating_cards)
        self.animating_cards.draw()
        for card in self.animating_cards:
            card.draw_modifier()

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
            cards_in_deck = len(self.deck_manager.draw_pile)
            s, m, desc, coin_bonus = scoring.calculate_hand_score(
                self.hand_list, self.joker_list, self.run_discards, cards_in_deck
            )
            total = s * m
            self.btn_score.text = f"PLAY HAND\n{s} x {m} = {total}"
            if coin_bonus > 0:
                self.btn_score.text += f"\n(+${coin_bonus})"
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
        elif self.state == GameState.PACK_OPENING:
            for btn in self.btn_pack_mods: btn.check_mouse_hover(x, y)
            self.btn_pack_skip.check_mouse_hover(x, y)
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
                    self.buy_shop_item(i)
                    return
            if self.btn_next_round and self.btn_next_round.is_clicked(x, y):
                self.round_level += 1
                self.target_score = int(self.target_score * 1.5)
                self.start_new_round()
                return

        elif self.state == GameState.PACK_OPENING:
            if self.btn_pack_skip.is_clicked(x, y):
                self.state = GameState.SHOPPING
                self.pack_card_list.clear()
                return
            
            for i, btn in enumerate(self.btn_pack_mods):
                if btn.is_clicked(x, y):
                    self.apply_pack_modifier(i)
                    return
            
            hit = arcade.get_sprites_at_point((x, y), self.pack_card_list)
            if hit:
                card = hit[0]
                if card.is_selected:
                    card.is_selected = False
                else:
                    num_selected = len([c for c in self.pack_card_list if c.is_selected])
                    if num_selected < 2:
                        card.is_selected = True
                    else:
                        self.message = "Select only 2 cards!"

        elif self.state == GameState.GAME_OVER:
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

    def reposition_hand(self):
        self.hand_list.sort(key=lambda c: (c.value, c.suit))
        
        start_x = (config.SCREEN_WIDTH - (len(self.hand_list) * (config.CARD_WIDTH + 20))) / 2 + config.CARD_WIDTH / 2
        for i, card in enumerate(self.hand_list):
            card.target_x = start_x + i * (config.CARD_WIDTH + 20)
            card.target_y = config.HAND_Y
            card.is_selected = False

    def reposition_jokers(self):
        start_x = config.SCREEN_WIDTH - 100
        for i, joker in enumerate(self.joker_list):
            tx = start_x - (i * (config.JOKER_WIDTH + 50))
            ty = config.SCREEN_HEIGHT - 220 
            joker.target_x = tx
            joker.target_y = ty
            joker.scale = 0.25

    def sell_joker(self):
        to_sell = [j for j in self.joker_list if j.is_selected]
        for joker in to_sell:
            self.coins += joker.sell_price
            joker.remove_from_sprite_lists()
        
        self.reposition_jokers()
        self.btn_sell.visible = False
        
        if self.state == GameState.SHOPPING:
            self.update_shop_buttons()

def main():
    window = WarGame()
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()