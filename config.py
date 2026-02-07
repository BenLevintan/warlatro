# config.py
import arcade

# --- Constants ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 900
SCREEN_TITLE = "Warlatro: Roguelike War (Retro Edition)"

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

# Animation Physics
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
COLOR_SHADOW = (0, 0, 0, 100)
COLOR_TOOLTIP_BG = (20, 20, 20, 230) 

# --- Joker Definitions ---
JOKER_DATA = {
    "pear_up": {
        "name": "Pear-Up", "cost": 4, "desc": "+8 Mult if Pair", 
        "file": ":resources:images/items/gold_1.png"
    },
    "helping_hand": {
        "name": "Helping Hand", "cost": 5, "desc": "+1 Hand per Round", 
        "file": ":resources:images/items/gemBlue.png"
    },
    "triple_treat": {
        "name": "Triple Treat", "cost": 4, "desc": "+12 Mult if 3-of-a-Kind", 
        "file": ":resources:images/items/gemRed.png"
    },
    "multi_python": {
        "name": "Multi Python", "cost": 7, "desc": "x2 Mult if 3-card Straight", 
        "file": ":resources:images/items/gemGreen.png"
    },
    "inflation": {
        "name": "Inflation", "cost": 6, "desc": "+12 Mult if Hand <= 4 cards", 
        "file": ":resources:images/items/gemYellow.png"
    }
}

# --- Shaders ---
VERTEX_SHADER = """
#version 330
in vec2 in_vert;
in vec2 in_uv;
out vec2 v_uv;
void main() {
    gl_Position = vec4(in_vert, 0.0, 1.0);
    v_uv = in_uv;
}
"""

FRAGMENT_SHADER = """
#version 330
uniform sampler2D texture0;
uniform float pixel_size;
uniform float time;
uniform vec2 screen_size;

in vec2 v_uv;
out vec4 f_color;

void main() {
    vec2 pixels = screen_size / pixel_size;
    vec2 uv = floor(v_uv * pixels) / pixels;
    vec4 color = texture(texture0, uv);

    float scanline = sin((v_uv.y * screen_size.y * 0.5) + (time * 5.0));
    float scan_intensity = 0.92 + (0.08 * scanline);
    color.rgb *= scan_intensity;

    float dist = distance(v_uv, vec2(0.5, 0.5));
    color.rgb *= smoothstep(0.8, 0.35, dist * 0.8);

    f_color = color;
}
"""