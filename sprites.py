# sprites.py
import arcade
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
        self.should_despawn = False 

    def update(self, delta_time: float = 1/60):
        """ Arcade calls this automatically every frame when list.update() is used """
        
        # 1. Spring Physics Calculation
        dx = self.target_x - self.center_x
        dy = self.target_y - self.center_y
        
        force_x = dx * config.STIFFNESS
        force_y = dy * config.STIFFNESS
        
        self.vel_x = (self.vel_x + force_x) * config.DAMPING
        self.vel_y = (self.vel_y + force_y) * config.DAMPING
        
        self.center_x += self.vel_x
        self.center_y += self.vel_y

        # 2. Despawn Logic (fly off screen)
        if self.should_despawn:
            if (self.center_y < -200 or self.center_y > config.SCREEN_HEIGHT + 200):
                self.remove_from_sprite_lists()