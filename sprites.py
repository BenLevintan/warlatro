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
        
        self.target_x = 0
        self.target_y = 0
        self.vel_x = 0
        self.vel_y = 0
        self._phys_x = 0
        self._phys_y = 0
        self.float_phase = random.uniform(0, 6.28)
        self.rot_phase = random.uniform(0, 6.28)
        self.timer = 0.0

    def update(self, delta_time: float = 1/60):
        self.timer += delta_time
        dx = self.target_x - self._phys_x
        dy = self.target_y - self._phys_y
        self.vel_x = (self.vel_x + dx * config.STIFFNESS) * config.DAMPING
        self.vel_y = (self.vel_y + dy * config.STIFFNESS) * config.DAMPING
        self._phys_x += self.vel_x
        self._phys_y += self.vel_y
        
        float_offset = math.sin(self.timer * config.FLOAT_SPEED + self.float_phase) * config.FLOAT_RANGE
        rot_offset = math.sin(self.timer * config.JOKER_ROT_SPEED + self.rot_phase) * config.JOKER_ROT_RANGE
        
        self.center_x = self._phys_x
        self.center_y = self._phys_y + float_offset
        self.angle = rot_offset

# --- Helper for Shop ---
class Pack(arcade.Sprite):
    """ Represents a Booster Pack in the Shop """
    def __init__(self, scale=1.0):
        # We use a placeholder image for packs if a specific one isn't set
        # Using a gem texture from built-in resources as a fallback visual
        super().__init__(":resources:images/items/gemRed.png", scale)
        self.name = "Standard Pack"
        self.desc = "Choose 1 of 2 modifiers\nfor selected cards."
        self.cost = 6 # Default, though usually set by shop logic
        self.is_selected = False
        self.is_hovered = False

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
        
        # --- Modifiers ---
        self.modifier = None # "bonus_chips", "mult_plus", "destroy"

        # --- Physics Properties ---
        self.target_x = 0
        self.target_y = 0
        self.vel_x = 0
        self.vel_y = 0
        self._phys_x = 0
        self._phys_y = 0
        self.should_despawn = False 
        self.float_phase = random.uniform(0, 6.28)
        self.timer = 0.0

    def update(self, delta_time: float = 1/60):
        self.timer += delta_time
        dx = self.target_x - self._phys_x
        dy = self.target_y - self._phys_y
        self.vel_x = (self.vel_x + dx * config.STIFFNESS) * config.DAMPING
        self.vel_y = (self.vel_y + dy * config.STIFFNESS) * config.DAMPING
        self._phys_x += self.vel_x
        self._phys_y += self.vel_y

        if self.should_despawn:
            self.center_x = self._phys_x
            self.center_y = self._phys_y
            if (self.center_y < -200 or self.center_y > config.SCREEN_HEIGHT + 200):
                self.remove_from_sprite_lists()
        else:
            float_offset = math.sin(self.timer * config.FLOAT_SPEED + self.float_phase) * config.FLOAT_RANGE
            self.center_x = self._phys_x
            self.center_y = self._phys_y + float_offset

    def draw_modifier(self):
        """ Manually draw indicator for modifier on top of card """
        if self.modifier:
            data = config.MODIFIER_DATA[self.modifier]
            
            # Draw colored border
            arcade.draw_rect_outline(
                arcade.XYWH(self.center_x, self.center_y, self.width, self.height),
                data['color'], 
                3
            )
            
            # Draw text badge (Without stroke_color to prevent crashes on older arcade versions)
            arcade.draw_text(
                data['name'][:4], # Abbreviate
                self.center_x, 
                self.center_y + 40, 
                data['color'], 
                10, 
                bold=True, 
                anchor_x="center"
            )