import random
import arcade
import config
import sprites
import ui_elements

class AudioManager:
    """ Handles all sound effects and music cross-fading """
    def __init__(self):
        # Load sounds safely
        try:
            self.bg_music = arcade.Sound(config.MUSIC_BG)
            self.store_music = arcade.Sound(config.MUSIC_STORE)
            self.game_over_music = arcade.Sound(config.MUSIC_GAME_OVER)
            self.card_sound = arcade.Sound(config.SOUND_CARD)
            self.play_hand_sound = arcade.Sound(config.SOUND_PLAY_HAND)
            self.buy_joker_sound = arcade.Sound(config.SOUND_BUY_JOKER) # NEW
            self.mod_sound = arcade.Sound(config.SOUND_MOD)             # NEW
        except Exception as e:
            print(f"Warning: Audio file missing or unreadable. {e}")
            self.bg_music = None
            self.store_music = None
            self.game_over_music = None
            self.card_sound = None
            self.play_hand_sound = None
            self.buy_joker_sound = None
            self.mod_sound = None

        # Track active players so we can manipulate volume
        self.bg_player = None
        self.store_player = None
        self.game_over_player = None
        
        # Fading targets
        self.base_volume = 0.5   
        self.bg_target_volume = self.base_volume
        self.store_target_volume = 0.0
        self.game_over_target_volume = 0.0
        
        self.fade_speed = 0.8    

    def play_card_sound(self):
        if self.card_sound:
            pitch_speed = random.uniform(0.85, 1.2)
            self.card_sound.play(volume=0.6, speed=pitch_speed)

    def play_hand_fx(self):
        if self.play_hand_sound:
            self.play_hand_sound.play(volume=0.8) 

    # --- NEW SOUND METHODS ---
    def play_buy_joker_fx(self):
        if self.buy_joker_sound:
            self.buy_joker_sound.play(volume=0.8)
            
    def play_mod_fx(self):
        if self.mod_sound:
            self.mod_sound.play(volume=1)

    # --- MUSIC FADING ---
    def start_bg_music(self):
        self.bg_target_volume = self.base_volume
        self.store_target_volume = 0.0
        self.game_over_target_volume = 0.0
        
        if self.bg_music:
            if self.bg_player:
                try: self.bg_player.pause()
                except Exception: pass
            self.bg_player = self.bg_music.play(volume=0.0, loop=True)

    def enter_store(self):
        self.bg_target_volume = 0.0
        self.store_target_volume = self.base_volume
        self.game_over_target_volume = 0.0
        
        if self.store_music:
            if self.store_player:
                try: self.store_player.pause()
                except Exception: pass
            self.store_player = self.store_music.play(volume=0.0, loop=True)

    def exit_store(self):
        self.start_bg_music()

    def enter_game_over(self):
        self.bg_target_volume = 0.0
        self.store_target_volume = 0.0
        self.game_over_target_volume = self.base_volume
        
        if self.game_over_music:
            if self.game_over_player:
                try: self.game_over_player.pause()
                except Exception: pass
            self.game_over_player = self.game_over_music.play(volume=0.0, loop=True)

    def update(self, delta_time):
        if self.bg_player:
            try:
                if self.bg_player.volume < self.bg_target_volume:
                    self.bg_player.volume = min(self.bg_target_volume, self.bg_player.volume + self.fade_speed * delta_time)
                elif self.bg_player.volume > self.bg_target_volume:
                    self.bg_player.volume = max(self.bg_target_volume, self.bg_player.volume - self.fade_speed * delta_time)
            except Exception: pass

        if self.store_player:
            try:
                if self.store_player.volume < self.store_target_volume:
                    self.store_player.volume = min(self.store_target_volume, self.store_player.volume + self.fade_speed * delta_time)
                elif self.store_player.volume > self.store_target_volume:
                    self.store_player.volume = max(self.store_target_volume, self.store_player.volume - self.fade_speed * delta_time)
            except Exception: pass

        if self.game_over_player:
            try:
                if self.game_over_player.volume < self.game_over_target_volume:
                    self.game_over_player.volume = min(self.game_over_target_volume, self.game_over_player.volume + self.fade_speed * delta_time)
                elif self.game_over_player.volume > self.game_over_target_volume:
                    self.game_over_player.volume = max(self.game_over_target_volume, self.game_over_player.volume - self.fade_speed * delta_time)
            except Exception: pass

class DeckManager:
    def __init__(self):
        self.master_deck = []
        self.draw_pile = []
        self.discard_pile = []
        self._create_initial_deck()

    def _create_initial_deck(self):
        suits = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        for suit in suits:
            for rank in ranks:
                card = sprites.Card(suit, rank, config.CARD_SCALE)
                self.master_deck.append(card)

    def start_round(self, visual_card_list):
        self.draw_pile = [c for c in self.master_deck if c.modifier != "destroy"]
        self.discard_pile = []
        random.shuffle(self.draw_pile)
        
        for card in self.draw_pile:
            card.should_despawn = False
            card.visible = False
            card.center_x = config.SCREEN_WIDTH + 200
            card.center_y = config.DRAWN_CARD_Y
            card.target_x = config.SCREEN_WIDTH + 200
            card.target_y = config.DRAWN_CARD_Y
            if card not in visual_card_list:
                visual_card_list.append(card)

    def draw_card(self, visual_card_list):
        if len(self.draw_pile) == 0 and len(self.discard_pile) > 0:
            self._recycle_discards(visual_card_list)

        if len(self.draw_pile) > 0:
            card = self.draw_pile.pop()
            card.visible = True
            card.should_despawn = False 
            return card
        return None

    def _recycle_discards(self, visual_card_list):
        self.draw_pile = self.discard_pile[:]
        self.discard_pile = []
        random.shuffle(self.draw_pile)
        
        for card in self.draw_pile:
            card.should_despawn = False 
            card.visible = False
            card.center_x = config.SCREEN_WIDTH + 200
            if card not in visual_card_list:
                visual_card_list.append(card)
    
    def get_deck_counts(self):
        total = len([c for c in self.master_deck if c.modifier != "destroy"])
        current = len(self.draw_pile) + len(self.discard_pile)
        return current, total

class ShopManager:
    def generate_shop(self, shop_list, shop_buttons, current_jokers):
        shop_list.clear()
        shop_buttons.clear()
        
        slots = ['Pack', 'Joker']
        slots.append(random.choice(['Pack', 'Joker']))
        
        owned_keys = [j.key for j in current_jokers]
        available_jokers = [k for k in config.JOKER_DATA.keys() if k not in owned_keys]
        
        start_x = config.SCREEN_WIDTH / 2 - 200
        for i, item_type in enumerate(slots):
            pos_x = start_x + (i * 200)
            pos_y = config.SCREEN_HEIGHT / 2 + 100
            
            if item_type == 'Pack':
                item = sprites.Pack(config.JOKER_SCALE)
                item.center_x = pos_x
                item.center_y = pos_y
                shop_list.append(item)
                
                btn = ui_elements.TextButton(pos_x, pos_y - 170, 120, 40, f"BUY ${config.PACK_COST}", config.COLOR_PURPLE)
                shop_buttons.append(btn)
                
            elif item_type == 'Joker' and available_jokers:
                key = random.choice(available_jokers)
                available_jokers.remove(key)
                
                item = sprites.Joker(key, config.JOKER_SCALE)
                item._phys_x = pos_x
                item._phys_y = pos_y
                item.target_x = pos_x
                item.target_y = pos_y
                shop_list.append(item)
                
                btn = ui_elements.TextButton(pos_x, pos_y - 170, 120, 40, f"BUY ${item.cost}", config.COLOR_BTN_SHOP)
                shop_buttons.append(btn)

    def get_pack_cards(self, master_deck):
        available = [c for c in master_deck if c.modifier != "destroy"]
        num = min(8, len(available))
        return random.sample(available, num)

    def get_pack_modifiers(self):
        keys = list(config.MODIFIER_DATA.keys())
        return random.sample(keys, 2)