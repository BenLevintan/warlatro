# sprites.py
import arcade
import random
import math
import config

class Joker(arcade.Sprite):
    def __init__(self, key, scale=1.0):
        data = config.JOKER_DATA[key]
        super().__init__(data['file'], scale)
        
        self.key = key
        self.name = data['name']
        self.cost = data['cost']
        self.desc = data['desc']
        self.sell_price = self.cost // 2
        self.is_selected = False
        self.is_hovered = False
        
        # --- Animation & Physics ---
        self.target_x = 0
        self.target_y = 0
        self.vel_x = 0
        self.vel_y = 0
        
        # Internal physics position (The "anchor" point before floating)
        self._phys_x = 0
        self._phys_y = 0
        
        # Randomize phase so they don't move in unison
        self.float_phase = random.uniform(0, 6.28)
        self.rot_phase = random.uniform(0, 6.28)
        self.timer = 0.0

    def update(self, delta_time: float = 1/60):
        self.timer += delta_time
        
        # 1. Physics (Move internal anchor towards target)
        dx = self.target_x - self._phys_x
        dy = self.target_y - self._phys_y
        
        self.vel_x = (self.vel_x + dx * config.STIFFNESS) * config.DAMPING
        self.vel_y = (self.vel_y + dy * config.STIFFNESS) * config.DAMPING
        
        self._phys_x += self.vel_x
        self._phys_y += self.vel_y
        
        # 2. Apply Visual Floating (Sine Wave)
        # y = base + sin(time * speed + offset) * range
        float_offset = math.sin(self.timer * config.FLOAT_SPEED + self.float_phase) * config.FLOAT_RANGE
        
        # 3. Apply Visual Rotation (Sine Wave)
        rot_offset = math.sin(self.timer * config.JOKER_ROT_SPEED + self.rot_phase) * config.JOKER_ROT_RANGE
        
        # Set final Arcade properties
        self.center_x = self._phys_x
        self.center_y = self._phys_y + float_offset
        self.angle = rot_offset

class Card(arcade.Sprite):
    def __init__(self, suit, rank, scale=1):
        self.suit = suit
        self.rank = rank
        
        # Calculate Value
        if rank in ['J', 'Q', 'K', 'A']:
            if rank == 'J': self.value = 11
            elif rank == 'Q': self.value = 12
            elif rank == 'K': self.value = 13
            elif rank == 'A': self.value = 14
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
        
        # Internal physics position
        self._phys_x = 0
        self._phys_y = 0
        
        self.should_despawn = False 
        
        # Animation
        self.float_phase = random.uniform(0, 6.28)
        self.timer = 0.0

    def update(self, delta_time: float = 1/60):
        self.timer += delta_time
        
        # 1. Physics
        dx = self.target_x - self._phys_x
        dy = self.target_y - self._phys_y
        
        self.vel_x = (self.vel_x + dx * config.STIFFNESS) * config.DAMPING
        self.vel_y = (self.vel_y + dy * config.STIFFNESS) * config.DAMPING
        
        self._phys_x += self.vel_x
        self._phys_y += self.vel_y

        # 2. Despawn Logic
        if self.should_despawn:
            # If flying off screen, don't float, just move
            self.center_x = self._phys_x
            self.center_y = self._phys_y
            if (self.center_y < -200 or self.center_y > config.SCREEN_HEIGHT + 200):
                self.remove_from_sprite_lists()
        else:
            # 3. Apply Floating if staying on screen
            float_offset = math.sin(self.timer * config.FLOAT_SPEED + self.float_phase) * config.FLOAT_RANGE
            self.center_x = self._phys_x
            self.center_y = self._phys_y + float_offset