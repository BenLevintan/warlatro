import arcade
import math
import config

class TextButton:
    def __init__(self, cx, cy, width, height, text, color=config.COLOR_BTN_DEFAULT, text_color=config.COLOR_WHITE):
        self.center_x = cx
        self.center_y = cy
        self.width = width
        self.height = height
        self.text = "  " + text 
        self.base_color = color
        self.highlight_color = config.COLOR_BTN_HOVER
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
        arcade.draw_rect_outline(rect, config.COLOR_WHITE, 2)

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


def get_rotated_points(cx, cy, w, h, angle_deg):
    """ Helper to calculate the 4 corners of a rotated rectangle """
    angle_rad = math.radians(angle_deg)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    # Half dimensions
    hw = w / 2
    hh = h / 2
    
    # Unrotated corners relative to center
    corners = [
        (hw, hh),
        (-hw, hh),
        (-hw, -hh),
        (hw, -hh)
    ]
    
    rotated_points = []
    for x, y in corners:
        # Rotate
        rx = x * cos_a - y * sin_a
        ry = x * sin_a + y * cos_a
        # Translate
        rotated_points.append((cx + rx, cy + ry))
        
    return rotated_points


def draw_shadows(sprite_list):
    """ Draws a drop shadow for every sprite, accounting for rotation and scale """
    for sprite in sprite_list:
        
        # Handle safe scale extraction
        scale = sprite.scale
        if isinstance(scale, (tuple, list)):
            scale = scale[0]
            
        width = sprite.width
        height = sprite.height
        
        if hasattr(sprite, 'texture') and sprite.texture:
            width = sprite.texture.width * scale
            height = sprite.texture.height * scale

        # Calculate rotated points manually
        points = get_rotated_points(
            sprite.center_x + 5,
            sprite.center_y - 5,
            width,
            height,
            -sprite.angle  # FIXED: Negated angle to sync shadow rotation
        )

        arcade.draw_polygon_filled(points, config.COLOR_SHADOW)


def draw_tooltip(hovered_joker, mouse_x, mouse_y):
    if not hovered_joker:
        return

    name_text = hovered_joker.name
    desc_text = hovered_joker.desc
    
    width = 220
    height = 80

    tip_x = mouse_x + 20
    tip_y = mouse_y - 20

    if tip_x + width > config.SCREEN_WIDTH:
            tip_x = mouse_x - width - 20
    
    bg_rect = arcade.XYWH(tip_x + width/2, tip_y - height/2, width, height)
    arcade.draw_rect_filled(bg_rect, config.COLOR_TOOLTIP_BG)
    arcade.draw_rect_outline(bg_rect, config.COLOR_WHITE, 1)
    
    arcade.draw_text(name_text, tip_x + 10, tip_y - 25, config.COLOR_GOLD, 14, bold=True)
    arcade.draw_text(desc_text, tip_x + 10, tip_y - 50, config.COLOR_WHITE, 12)