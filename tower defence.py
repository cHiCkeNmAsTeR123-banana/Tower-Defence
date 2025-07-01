import pygame
import math
import random
import json
import array
import os         # <-- Add this
import asyncio    # <-- Add this

# --- This tells Pygame to draw on the webpage ---
os.environ['PYGAME_DISPLAY'] = "canvas"
os.environ['PYGAME_CANVAS_ID'] = "pygame-container"
async def main():
    particles = []
    floating_texts = []
    death_effects = []
    lightning_effects = [] 
    nova_effects = []      
    
    FPS = 60
    pygame.init()
    pygame.mixer.init()
    camera_zoom = 1.0
    
    def draw_background_and_path(win, grid_color, horizon_y, map_grid):
        width, height = win.get_size()
    
        sky_color, horizon_color, near_floor_color = (10,10,30), (40,40,80), (0,0,10)
        win.fill(sky_color)
        for y in range(int(horizon_y), height):
            ratio = (y - horizon_y) / (height - horizon_y)
            color = ( int(horizon_color[0]*(1-ratio) + near_floor_color[0]*ratio), int(horizon_color[1]*(1-ratio) + near_floor_color[1]*ratio), int(horizon_color[2]*(1-ratio) + near_floor_color[2]*ratio) )
            pygame.draw.line(win, color, (0,y), (width,y))
    
        path_color = (180, 180, 200); land_color = (40, 40, 80)
        spawn_color = (200, 200, 100); exit_color = (200, 100, 100)
    
        if map_grid:
            for r in range(GRID_ROWS):
                for c in range(GRID_COLS):
    
                    p1 = get_screen_coords_for_grid_cell(r - 0.5, c - 0.5, horizon_y, width, height, GRID_ROWS, GRID_COLS, camera_zoom)
                    p2 = get_screen_coords_for_grid_cell(r - 0.5, c + 0.5, horizon_y, width, height, GRID_ROWS, GRID_COLS, camera_zoom)
                    p3 = get_screen_coords_for_grid_cell(r + 0.5, c + 0.5, horizon_y, width, height, GRID_ROWS, GRID_COLS, camera_zoom)
                    p4 = get_screen_coords_for_grid_cell(r + 0.5, c - 0.5, horizon_y, width, height, GRID_ROWS, GRID_COLS, camera_zoom)
                    
                    tile_type = map_grid[r][c]
                    if tile_type == 1: color = path_color
                    elif tile_type == 2: color = spawn_color
                    elif tile_type == 3: color = exit_color
                    else: color = land_color
                    
                    pygame.draw.polygon(win, color, [p1, p2, p3, p4])
                    pygame.draw.polygon(win, grid_color, [p1, p2, p3, p4], 1)
    def get_screen_coords_for_grid_cell(row, col, horizon_y, width, height, num_rows, num_cols, zoom):
        try:
            exponent = 2.0 / zoom 
            
            y_ratio_below = (row / num_rows)**exponent
            y_ratio_above = ((row + 1) / num_rows)**exponent
            y_below = horizon_y + (height - horizon_y) * y_ratio_below
            y_above = horizon_y + (height - horizon_y) * y_ratio_above
            snapped_y = (y_below + y_above) / 2
    
            vanishing_point_x = width / 2
            perspective_stretch_at_zoom = PERSPECTIVE_STRETCH / zoom
            
            x_on_horizon_left = (width / num_cols) * col
            x_on_horizon_right = (width / num_cols) * (col + 1)
            
            end_x_left = vanishing_point_x + (x_on_horizon_left - vanishing_point_x) * perspective_stretch_at_zoom
            end_x_right = vanishing_point_x + (x_on_horizon_right - vanishing_point_x) * perspective_stretch_at_zoom
            
            y_ratio_on_line = (snapped_y - horizon_y) / (height - horizon_y)
            
            x_at_depth_left = vanishing_point_x + (end_x_left - vanishing_point_x) * y_ratio_on_line
            x_at_depth_right = vanishing_point_x + (end_x_right - vanishing_point_x) * y_ratio_on_line
    
            snapped_x = (x_at_depth_left + x_at_depth_right) / 2
            return (int(snapped_x), int(snapped_y))
        except (ValueError, TypeError, ZeroDivisionError):
            return (0, 0)
    def get_grid_indices_from_pos(mx, my, horizon_y, width, height, num_rows, num_cols, zoom):
        if my <= horizon_y: return None
    
        exponent = 2.0 / zoom
        
        y_ratio = (my - horizon_y) / (height - horizon_y)
        y_ratio = max(0, min(1, y_ratio))
        row_index = int((y_ratio**(1.0/exponent)) * num_rows)
        row_index = min(row_index, num_rows - 1)
    
        vanishing_point_x = width / 2
        y_ratio_on_line = (my - horizon_y) / (height - horizon_y)
        perspective_stretch_at_zoom = PERSPECTIVE_STRETCH / zoom
    
        vertical_line_x_at_y = []
        for i in range(num_cols + 1):
            x_on_horizon = (width / num_cols) * i
            end_x_at_bottom = vanishing_point_x + (x_on_horizon - vanishing_point_x) * perspective_stretch_at_zoom
            x_at_y = vanishing_point_x + (end_x_at_bottom - vanishing_point_x) * y_ratio_on_line
            vertical_line_x_at_y.append(x_at_y)
    
        col_index = -1
        for i in range(len(vertical_line_x_at_y) - 1):
            if vertical_line_x_at_y[i] <= mx < vertical_line_x_at_y[i+1]:
                col_index = i
                break
        
        if col_index == -1: return None
        return (row_index, col_index)
    def draw_hexagon_outline(surface, color, center, radius, width=1):
        depth_ratio = max(0, (center[1] - (NATIVE_HEIGHT * 0.4))) / (NATIVE_HEIGHT - (NATIVE_HEIGHT * 0.4))
        scale_factor = 0.3 + depth_ratio * 0.7
        squash_factor = scale_factor * 0.8 
    
        points = []
        for i in range(6):
            angle_deg = 60 * i
            angle_rad = math.pi / 180 * angle_deg
            point_x = center[0] + radius * math.cos(angle_rad)
    
            point_y = center[1] + radius * math.sin(angle_rad) * squash_factor
            points.append((point_x, point_y))
        pygame.draw.polygon(surface, color, points, width)
    
    
    def generate_path_from_grid(map_data):
    
        grid = map_data["grid"]
        
        start_pos = None
        for r, row_data in enumerate(grid):
            for c, tile in enumerate(row_data):
                if tile == 2:
                    start_pos = (r, c)
                    break
            if start_pos:
                break
                
        if not start_pos:
            return []
    
        path_waypoints = []
        current_pos = start_pos
        visited = {current_pos}
    
        while True:
            screen_coords = get_screen_coords_for_grid_cell(
                current_pos[0], current_pos[1], 
                NATIVE_HEIGHT * 0.4, NATIVE_WIDTH, NATIVE_HEIGHT, 
                GRID_ROWS, GRID_COLS, camera_zoom
            )
            path_waypoints.append(screen_coords)
    
            if grid[current_pos[0]][current_pos[1]] == 3:
                break
    
            found_next = False
            for dr, dc in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                next_r, next_c = current_pos[0] + dr, current_pos[1] + dc
                
                if 0 <= next_r < len(grid) and 0 <= next_c < len(grid[0]) and (next_r, next_c) not in visited:
                    if grid[next_r][next_c] in [1, 3]:
                        current_pos = (next_r, next_c)
                        visited.add(current_pos)
                        found_next = True
                        break
            
            if not found_next:
                break
                
        return path_waypoints
    
    def generate_sound(frequency, duration_ms, volume=0.5, waveform='sine', decay_speed=3.0):
        sample_rate = 22050
        n_samples = int(sample_rate * (duration_ms / 1000.0))
        buf = array.array('h', [0] * n_samples)
        amplitude = 32767 * volume
        for i in range(n_samples):
            time_in_seconds = float(i) / sample_rate
            wave = 0
            if waveform == 'square':
                wave = 1 if math.sin(2 * math.pi * frequency * time_in_seconds) > 0 else -1
            else:
                wave = math.sin(2 * math.pi * frequency * time_in_seconds)
            decay = math.exp(-decay_speed * time_in_seconds)
            buf[i] = int(wave * amplitude * decay)
        sound = pygame.mixer.Sound(buffer=buf)
        return sound
    
    def generate_noise_hit(duration_ms, volume=0.5, decay_speed=10.0, frequency_ish=440):
        sample_rate = 22050
        n_samples = int(sample_rate * (duration_ms / 1000.0))
        buf = array.array('h', [0] * n_samples)
        amplitude = 32767 * volume
        for i in range(n_samples):
            time_in_seconds = float(i) / sample_rate
            noise = random.uniform(-1, 1)
            noise_tint = math.sin(2 * math.pi * frequency_ish * time_in_seconds)
            decay = math.exp(-decay_speed * time_in_seconds)
            buf[i] = int((noise * 0.7 + noise_tint * 0.3) * amplitude * decay)
        sound = pygame.mixer.Sound(buffer=buf)
        return sound
    
    
    def generate_barrel_sprite(width, height, base_tower_color):
        sprite_surface = pygame.Surface((width + 2, height + 4), pygame.SRCALPHA)
        shadow, metal = (80, 80, 80), (150, 150, 150)
        barrel_body_rect = pygame.Rect(0, 2, width, height)
        pygame.draw.rect(sprite_surface, shadow, barrel_body_rect)
        pygame.draw.rect(sprite_surface, metal, barrel_body_rect.inflate(-2, -2))
        pygame.draw.line(sprite_surface, base_tower_color, (2, 3), (width - 2, 3), 1)
        muzzle_ellipse_rect = pygame.Rect(-1, -2, width + 4, 8)
        pygame.draw.ellipse(sprite_surface, (40, 40, 40), muzzle_ellipse_rect)
        pygame.draw.ellipse(sprite_surface, (80, 80, 80), muzzle_ellipse_rect.inflate(-4, -4))
        return sprite_surface
    
    def generate_tower_base(base_color, radius):
        side_color = (max(0, base_color[0] - 60), max(0, base_color[1] - 60), max(0, base_color[2] - 60))
        highlight_color = (min(255, base_color[0] + 50), min(255, base_color[1] + 50), min(255, base_color[2] + 50))
        cylinder_height, top_face_height = 8, 12
        surface_width, surface_height = radius * 2, cylinder_height + top_face_height
        sprite_surface = pygame.Surface((surface_width, surface_height), pygame.SRCALPHA)
        body_rect = pygame.Rect(0, int(top_face_height / 2), surface_width, cylinder_height)
        pygame.draw.rect(sprite_surface, side_color, body_rect)
        bottom_ellipse_rect = pygame.Rect(0, cylinder_height, surface_width, top_face_height)
        pygame.draw.ellipse(sprite_surface, side_color, bottom_ellipse_rect)
        top_ellipse_rect = pygame.Rect(0, 0, surface_width, top_face_height)
        pygame.draw.ellipse(sprite_surface, base_color, top_ellipse_rect)
        highlight_arc_rect = pygame.Rect(int(radius * 0.3), 2, int(radius * 1.4), top_face_height - 2)
        pygame.draw.arc(sprite_surface, highlight_color, highlight_arc_rect, math.radians(30), math.radians(150), 2)
        return sprite_surface
    
    def generate_enemy_sprite(base_color, size):
        side_color1 = (max(0, base_color[0] - 40), max(0, base_color[1] - 40), max(0, base_color[2] - 40))
        side_color2 = (max(0, base_color[0] - 80), max(0, base_color[1] - 80), max(0, base_color[2] - 80))
        w, h = size, size
        sprite_surface = pygame.Surface((w * 2, h * 2), pygame.SRCALPHA)
        top_p, side1_p, side2_p = [(w,0),(w*2,h*0.5),(w,h),(0,h*0.5)], [(0,h*0.5),(w,h),(w,h*2),(0,h*1.5)], [(w,h),(w*2,h*0.5),(w*2,h*1.5),(w,h*2)]
        pygame.draw.polygon(sprite_surface, side_color1, side1_p)
        pygame.draw.polygon(sprite_surface, side_color2, side2_p)
        pygame.draw.polygon(sprite_surface, base_color, top_p)
        return sprite_surface
    
    def generate_bullet_sprite(color, tail_color):
        width, height = 10, 16
        bullet_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        tail_points, head_points = [(width/2,height),(0,0),(width,0)], [(width/2,4),(width-1,0),(1,0)]
        pygame.draw.polygon(bullet_surface, (*tail_color, 120), tail_points)
        pygame.draw.polygon(bullet_surface, color, head_points)
        return bullet_surface
    
    def create_vectoid_background(width, height):
        background = pygame.Surface((width, height))
        horizon_y = height * 0.4
        sky_color, horizon_color, near_floor_color = (10,10,30), (40,40,80), (0,0,10)
        background.fill(sky_color)
        for y in range(int(horizon_y), height):
            ratio = (y - horizon_y) / (height - horizon_y)
            color = (int(horizon_color[0]*(1-ratio)+near_floor_color[0]*ratio), int(horizon_color[1]*(1-ratio)+near_floor_color[1]*ratio), int(horizon_color[2]*(1-ratio)+near_floor_color[2]*ratio))
            pygame.draw.line(background, color, (0,y), (width,y))
        return background
    
    def draw_3d_grid(win, color, horizon_y, height):
        num_horizontal_lines, num_vertical_lines = GRID_ROWS, GRID_COLS
        vanishing_point = (NATIVE_WIDTH / 2, horizon_y)
        for i in range(1, num_horizontal_lines + 1):
            y = horizon_y + (height - horizon_y) * (i / num_horizontal_lines)**2
            pygame.draw.line(win, color, (0, int(y)), (NATIVE_WIDTH, int(y)))
        for i in range(num_vertical_lines + 1):
            x_on_horizon = (NATIVE_WIDTH / num_vertical_lines) * i
            end_x = vanishing_point[0] + (x_on_horizon - vanishing_point[0]) * (height / (height-horizon_y))
            pygame.draw.line(win, color, vanishing_point, (end_x, height))
    NATIVE_WIDTH, NATIVE_HEIGHT = 1000, 600
    GRID_ROWS = 20  
    GRID_COLS = 16  
    PERSPECTIVE_STRETCH = 2.5 
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    display = pygame.Surface((NATIVE_WIDTH, NATIVE_HEIGHT))
    WIDTH, HEIGHT = NATIVE_WIDTH, NATIVE_HEIGHT
    
    WHITE, RED, GREEN, BLACK, GRAY, BLUE, YELLOW, PURPLE, ORANGE = (255,255,255),(255,0,0),(0,255,0),(0,0,0),(150,150,150),(0,0,255),(255,255,0),(128,0,128),(255,165,0)
    
    try:
        click_sound = generate_sound(frequency=1500, duration_ms=50, volume=0.1, decay_speed=8)
        shoot_sound = generate_sound(frequency=660, duration_ms=100, volume=0.05, waveform='square', decay_speed=5)
        hit_sound = generate_noise_hit(duration_ms=100, volume=0.15, decay_speed=10)
        death_sound = generate_sound(frequency=220, duration_ms=300, volume=0.25, decay_speed=4)
        airstrike_sound = generate_noise_hit(duration_ms=500, volume=0.4, decay_speed=5)
        NORMAL_BULLET_SPRITE = generate_bullet_sprite(YELLOW, ORANGE)
        VAMPIRE_BULLET_SPRITE = generate_bullet_sprite(RED, PURPLE)
        pygame.mixer.music.load("random soundtrack.wav") 
        pygame.mixer.music.set_volume(0.1)
        sounds_loaded = True
    except Exception as e:
        print(f"Cannot load or generate audio: {e}")
        sounds_loaded = False
    
    MAPS = {
        "Twisty Path": {
            "grid": [
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1],
                [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
                [0, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1, 0, 0, 1],
                [0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1],
                [0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1],
                [0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1],
                [0, 0, 1, 0, 0, 1, 1, 1, 3, 0, 1, 1, 1, 0, 0, 1],
                [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                [0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                [1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], 
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            ],
            "description": "A long, winding path with a central exit.",
            "difficulty": "Easy"
        },
        "Classic U": {
            "grid": [
                [4, 4, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4, 4],
                [4, 4, 1, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 1, 4, 4],
                [4, 4, 1, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 1, 4, 4],
                [4, 4, 1, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 1, 4, 4],
                [4, 4, 1, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 1, 4, 4],
                [4, 4, 1, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 1, 4, 4],
                [4, 4, 1, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 1, 4, 4],
                [4, 4, 1, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 1, 4, 4],
                [4, 4, 1, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 1, 4, 4],
                [4, 4, 1, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 1, 4, 4],
                [4, 4, 1, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 1, 4, 4],
                [4, 4, 1, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 1, 4, 4],
                [4, 4, 1, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 1, 4, 4],
                [4, 4, 1, 4, 0, 0, 0, 0, 0, 0, 0, 0, 4, 1, 4, 4],
                [4, 4, 1, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 1, 4, 4],
                [4, 4, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 4, 4],
                [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 4, 4],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            ],
            "description": "A long U-shaped path that rewards long-range towers.",
            "difficulty": "Medium"
        },
        "Diagonal Cross": {
            "grid": [
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            ],
            "description": "A very direct diagonal path. High damage is a must.",
            "difficulty": "Hard"
        }
    }
    PATH = None
    font = pygame.font.SysFont("Arial", 20)
    
    class EnemyType:
        def __init__(self, name, color, health, speed, cost, reward, size, description="", ability=None):
            self.name, self.color, self.health, self.speed, self.cost, self.reward, self.size, self.description, self.ability = name, color, health, speed, cost, reward, size, description, ability
    
    enemy_types = [
        EnemyType("Normal",GREEN,3,1.0,5,30,17,"A standard enemy unit."), EnemyType("Strong",RED,10,0.5,10,75,19,"Moves slowly but can absorb a significant amount of damage."),
        EnemyType("Speed",BLUE,2,2.0,7,50,15,"A fast-moving unit that can quickly overwhelm defenses."), EnemyType("Tiny",YELLOW,1,1.0,1,10,10,"Extremely weak, but appears in large numbers."),
        EnemyType("Miniboss",PURPLE,50,0.3,30,300,23,"A very tough unit that leads the charge.",ability="spawner"),
        EnemyType("Healer",WHITE,8,0.8,15,60,18,"Periodically heals nearby enemies.",ability="heal"), EnemyType("Armored",GRAY,12,0.7,20,80,20,"Plated armor reduces all incoming damage.",ability="armor"),
    ]
    
    
    class Enemy:
        def __init__(self, health, speed, color, reward, size, enemy_type):
            self.grid_r, self.grid_c = 0.0, 0.0
            self.x, self.y = 0, 0 
            for r, row_data in enumerate(current_map_grid):
                for c, tile in enumerate(row_data):
                    if tile == 2:
                        self.grid_r, self.grid_c = float(r), float(c)
                        break
    
            self.path_index, self.speed, self.health, self.max_health, self.color, self.reward, self.size, self.enemy_type = 0, speed, health, health, color, reward, size, enemy_type
            self.poison_timer, self.poison_damage_per_second, self.stun_timer, self.base_speed, self.slowed = 0,0,0,speed,False
            self.ability, self.ability_cooldown = self.enemy_type.ability, 0
            if self.ability=="spawner": self.tiny_spawn_timer,self.normal_spawn_timer,self.strong_spawn_timer,self.armored_spawn_timer = 2*FPS,5*FPS,10*FPS,20*FPS
            self.image = generate_enemy_sprite(self.color, self.size)
    
        def move(self, current_wave):
            if self.path_index >= len(PATH) - 1:
                return []
    
            target_x, target_y = PATH[self.path_index + 1]
            current_x, current_y = self.x, self.y
    
            dx, dy = target_x - current_x, target_y - current_y
            dist = math.hypot(dx, dy)
    
    
            depth_ratio = max(0, (self.y - (NATIVE_HEIGHT * 0.4))) / (NATIVE_HEIGHT - (NATIVE_HEIGHT * 0.4))
            current_speed = self.speed * (20 + 80 * depth_ratio) * (1/FPS) 
            
            if self.slowed:
                current_speed *= 0.5
            
            if dist < current_speed:
                self.path_index += 1
            else:
                self.x += (dx / dist) * current_speed
                self.y += (dy / dist) * current_speed
            
            newly_spawned = []
            if self.ability=="spawner":
                self.tiny_spawn_timer-=1
                if self.tiny_spawn_timer<=0:
                    tiny_type = next((e for e in enemy_types if e.name=="Tiny"),None)
                    if tiny_type: newly_spawned.append(Enemy(tiny_type.health*current_wave,tiny_type.speed,tiny_type.color,tiny_type.reward,tiny_type.size,tiny_type)); newly_spawned[-1].x,newly_spawned[-1].y=self.x,self.y
                    self.tiny_spawn_timer=2*FPS
            self.slowed=False
            for tower in towers:
                if tower.kind=="Frost" and math.hypot(tower.x-self.x,tower.y-self.y)<=tower.range: self.slowed=True; break
            if self.ability=="heal":
                if self.ability_cooldown > 0: self.ability_cooldown -= 1
                else:
                    for other_enemy in enemies:
                        if other_enemy is not self and math.hypot(self.x-other_enemy.x,self.y-other_enemy.y)<60:
                            if other_enemy.health < other_enemy.max_health:
                                other_enemy.health = min(other_enemy.max_health, other_enemy.health + 2)
                                floating_texts.append({"x": other_enemy.x + random.randint(-5, 5),"y": other_enemy.y,"text": "+","life": 30,"alpha": 255,"color": (0, 255, 0)})
                    self.ability_cooldown=3*FPS
            if self.poison_timer>0:
                self.health-=self.poison_damage_per_second/FPS; self.poison_timer-=1
                if hasattr(self,'poison_applier'): self.poison_applier.damage_points+=self.poison_damage_per_second/FPS; self.poison_applier.damage_done+=self.poison_damage_per_second/FPS
            if self.stun_timer>0: self.stun_timer-=1; return newly_spawned
            return newly_spawned
    
        def draw(self, win):
            horizon_y = NATIVE_HEIGHT * 0.4
            y_ratio = max(0, min(1, (self.y - horizon_y) / (NATIVE_HEIGHT - horizon_y)))
            grid_depth_ratio = y_ratio ** (camera_zoom / 2.0)
            scale_factor = 0.3 + grid_depth_ratio * 0.7
            scaled_width,scaled_height=int(self.image.get_width()*scale_factor),int(self.image.get_height()*scale_factor)
            if scaled_width>0 and scaled_height>0:
                scaled_image=pygame.transform.smoothscale(self.image,(scaled_width,scaled_height))
                img_rect=scaled_image.get_rect(center=(self.x,self.y))
                win.blit(scaled_image,img_rect.topleft)
                
            health_ratio=self.health/self.max_health
            bar_y=self.y-(scaled_height/2)-10
            pygame.draw.rect(win,(50,50,50),(self.x-15,bar_y,30,5))
            pygame.draw.rect(win,GREEN,(self.x-15,bar_y,int(30*health_ratio),5))
            if self.poison_timer > 0: draw_hexagon_outline(win, (0, 200, 0), (self.x, self.y), scaled_width * 0.7, 2)
            if self.stun_timer > 0: draw_hexagon_outline(win, (255, 255, 0), (self.x, self.y), scaled_width * 0.7, 2)
            if self.slowed: draw_hexagon_outline(win, (150, 255, 255), (self.x, self.y), scaled_width * 0.7, 2)
    
    
    class Tower:
        def __init__(self, grid_r, grid_c, color, cooldown, damage, range_, kind="Basic", level=1):
            self.grid_r, self.grid_c = grid_r, grid_c
            self.x, self.y = 0, 0 
    
            self.color, self.cooldown, self.damage, self.range, self.kind, self.level = color, cooldown, damage, range_, kind, level
            self.damage_done, self.damage_points, self.total_cost, self.cost, self.timer = 0,0,0,0,0
            self.damage_upgrade_cost, self.firerate_upgrade_cost, self.range_upgrade_cost = 25,30,20
            self.is_overcharged, self.target, self.angle = False,None,0
            self.base_image = generate_tower_base(self.color, 17)
            barrel_info = TOWER_TYPES[kind].get("barrel")
            if barrel_info: self.barrel_image = generate_barrel_sprite(barrel_info["width"], barrel_info["height"], self.color)
            else: self.barrel_image = None
            self.targeting_mode = "First"
    
        def upgrade(self):
            if self.level>=5: return
            self.level+=1
            self.damage*=1.5
            self.range+=20
            self.cooldown=max(5,int(self.cooldown*0.9))
            self.total_cost+=100*(self.level-1)
    
        def shoot(self, enemies, bullets):
            if self.timer > 0: self.timer -= 2 if self.is_overcharged else 1; return
            self.target = None
            if self.kind == "Flame" or self.kind == "Frost":
                has_fired = False
                for enemy in enemies:
                    if math.hypot(enemy.x - self.x, enemy.y - self.y) <= self.range:
                        enemy.health -= self.damage; has_fired = True
                if has_fired:
                    if self.kind == "Frost":
                        nova_effects.append({"x": self.x, "y": self.y, "radius": 10, "max_radius": self.range, "life": 25})
                    self.timer = self.cooldown
                return
            valid_targets = [e for e in enemies if math.hypot(e.x-self.x, e.y-self.y) <= self.range]
            if valid_targets:
                if self.targeting_mode == "First": self.target = valid_targets[0]
                elif self.targeting_mode == "Last": self.target = valid_targets[-1]
                elif self.targeting_mode == "Strongest": self.target = max(valid_targets, key=lambda e: e.health)
                elif self.targeting_mode == "Closest": self.target = min(valid_targets, key=lambda e: math.hypot(e.x-self.x, e.y-self.y))
                else: self.target = valid_targets[0]
                if sounds_loaded: shoot_sound.play()
                if self.kind=="Poison":
                    if self.target.poison_timer<=0: self.target.poison_timer,self.target.poison_damage_per_second,self.target.poison_applier=int(self.level*5*FPS),2*self.level,self
                elif self.kind=="Vampire": bullets.append(VampireBullet(self.x,self.y,self.target,self.damage,self))
                else: bullets.append(Bullet(self.x,self.y,self.target,self.damage,tower=self))
                self.timer=self.cooldown
    
        def draw(self, win):
            horizon_y = NATIVE_HEIGHT * 0.4
            y_ratio = max(0, min(1, (self.y - horizon_y) / (NATIVE_HEIGHT - horizon_y)))
            grid_depth_ratio = y_ratio ** (camera_zoom / 2.0)
            scale_factor = 0.3 + grid_depth_ratio * 0.7
            scaled_width = int(self.base_image.get_width() * scale_factor)
            scaled_height = int(self.base_image.get_height() * scale_factor)
            if scaled_width > 0 and scaled_height > 0:
                scaled_base = pygame.transform.smoothscale(self.base_image, (scaled_width, scaled_height))
                base_rect = scaled_base.get_rect(center=(self.x, self.y))
                win.blit(scaled_base, base_rect.topleft)
            if self.barrel_image:
                if self.target:
                    dx, dy = self.target.x - self.x, self.target.y - self.y
                    self.angle = math.degrees(math.atan2(-dy, dx)) - 90
                scaled_barrel_w = int(self.barrel_image.get_width() * scale_factor)
                scaled_barrel_h = int(self.barrel_image.get_height() * scale_factor)
                if scaled_barrel_w > 0 and scaled_barrel_h > 0:
                    scaled_barrel = pygame.transform.smoothscale(self.barrel_image, (scaled_barrel_w, scaled_barrel_h))
                    rotated_barrel = pygame.transform.rotate(scaled_barrel, self.angle)
                    barrel_pivot_offset = scaled_barrel_h * 0.4 
                    angle_rad = math.radians(self.angle + 90)
                    offset_x = barrel_pivot_offset * math.cos(angle_rad)
                    offset_y = -barrel_pivot_offset * math.sin(angle_rad)
                    barrel_rect = rotated_barrel.get_rect(center=(self.x + offset_x, self.y + offset_y))
                    win.blit(rotated_barrel, barrel_rect.topleft)
            level_text = font.render(str(self.level), True, WHITE)
            win.blit(level_text, (self.x - 5, self.y - scaled_height / 2 - 15))
            if self.damage_points >= self.firerate_upgrade_cost or self.damage_points >= self.damage_upgrade_cost or self.damage_points >= self.range_upgrade_cost:
                draw_hexagon_outline(win, RED, (self.x, self.y), scaled_width * 0.7, 2)
    class PoisonTower(Tower):
        def __init__(self,grid_r,grid_c,level=1): super().__init__(grid_r,grid_c,(0,150,0),int(FPS),0,150,kind="Poison",level=level)
    class ElectricTower(Tower):
        def __init__(self,grid_r,grid_c,level=1): super().__init__(grid_r,grid_c,(100,100,255),int(FPS/2),1,150,kind="Electric",level=level)
    class FrostTower(Tower):
        def __init__(self,grid_r,grid_c,level=1): super().__init__(grid_r,grid_c,(150,255,255),FPS,0.5,130,kind="Frost",level=level)
    class VampireTower(Tower):
        def __init__(self,grid_r,grid_c,level=1): super().__init__(grid_r,grid_c,(128,0,128),int(FPS/2),1,150,kind="Vampire",level=level)
    class FarmTower(Tower):
        def __init__(self,grid_r,grid_c,level=1):
            super().__init__(grid_r,grid_c,(255,215,0),int(FPS*5),0,0,kind="Farm",level=level)
            self.income=15
            for i in range(1,self.level): self.income=int(self.income*1.8)
        def upgrade(self):
            if self.level>=5: return
            super().upgrade(); self.income=int(self.income*1.8)
        def shoot(self,enemies,bullets): pass
    
     
    class Bullet:
        def __init__(self,x,y,target,damage,tower=None):
            self.x,self.y,self.target,self.damage,self.tower=x,y,target,damage,tower
            self.speed=8
            self.image=NORMAL_BULLET_SPRITE
        def move(self):
            if self.target.health <= 0 and self in bullets:
                bullets.remove(self)
                return
            dx,dy=self.target.x-self.x,self.target.y-self.y
            dist=math.hypot(dx,dy)
            if dist!=0: self.x+=dx/dist*self.speed; self.y+=dy/dist*self.speed
        def draw(self,win):
            img_rect=self.image.get_rect(center=(self.x,self.y)); win.blit(self.image,img_rect.topleft)
    
    class VampireBullet(Bullet):
        def __init__(self,x,y,target,damage,tower):
            super().__init__(x,y,target,damage,tower)
            self.image=VAMPIRE_BULLET_SPRITE
        def move(self):
            if self.target.health <= 0 and self in bullets:
                bullets.remove(self)
                return
            dx,dy=self.target.x-self.x,self.target.y-self.y
            dist=math.hypot(dx,dy)
            if dist!=0: self.x+=dx/dist*self.speed; self.y+=dy/dist*self.speed
            if math.hypot(self.x-self.target.x,self.y-self.target.y)<10:
                self.target.health-=self.damage
                global player_health
                player_health+=self.damage*0.5
                if self in bullets: bullets.remove(self)
    
    def snap_to_3d_grid(mx, my, horizon_y, width, height, num_rows, num_cols, zoom):
    
        indices = get_grid_indices_from_pos(mx, my, horizon_y, width, height, num_rows, num_cols, zoom)
        
        if indices:
            
            row, col = indices
            return get_screen_coords_for_grid_cell(row, col, horizon_y, width, height, num_rows, num_cols, zoom)
        
    
        return None
    MENU_SETS = {
        "default":["Next Wave","Normal","Machine Gun","Cannon","Missile","Advanced Towers","Abilities","Codex","Cancel"],
        "advanced":["Poison","Electric","Frost","Vampire","Flame","Farm","Next Wave","Abilities","Codex","Back","Cancel"],
        "abilities":["Airstrike","Global Freeze","Overcharge","Back"],
        "tower_selected":["Upgrade","Sell","Relocate","Upgrade Damage","Upgrade Firing Rate","Upgrade Range","Abilities","Codex","Cancel"],
    }
    
    def draw_menu(win,font,hovered_button,menu_labels):
        pygame.draw.rect(win,GRAY,(800,0,200,HEIGHT))
        button_rects=[]
        for i,label in enumerate(menu_labels):
            rect=pygame.Rect(810,10+i*50,180,45)
            button_rects.append((label,rect))
            color=(200,200,200) if hovered_button==i else (100,100,100)
            pygame.draw.rect(win,color,rect)
            text_color,display_label=WHITE,label
            if label=="Airstrike":
                if airstrike_cooldown>0: text_color,display_label=GRAY,f"Airstrike ({airstrike_cooldown//FPS}s)"
                elif money<PLAYER_ABILITIES["Airstrike"]["cost"]: text_color=GRAY
            elif label=="Global Freeze":
                if global_freeze_cooldown>0: text_color,display_label=GRAY,f"Global Freeze ({global_freeze_cooldown//FPS}s)"
                elif money<PLAYER_ABILITIES["Global Freeze"]["cost"]: text_color=GRAY
            elif label=="Overcharge":
                if overcharge_cooldown>0: text_color,display_label=GRAY,f"Overcharge ({overcharge_cooldown//FPS}s)"
                elif money<PLAYER_ABILITIES["Overcharge"]["cost"]: text_color=GRAY
            win.blit(font.render(display_label,True,text_color),(rect.x+10,rect.y+12))
            tower_button_kinds,ability_button_kinds=list(TOWER_TYPES.keys()),list(PLAYER_ABILITIES.keys())
            if hovered_button==i and (label in tower_button_kinds or label in ability_button_kinds):
                info,tooltip_lines=None,[]
                if label in PLAYER_ABILITIES: 
                    info=PLAYER_ABILITIES[label]
                    tooltip_lines=[f"Cost: ${info['cost']}",f"Cooldown: {info['cooldown']//FPS}s"]
                elif label in TOWER_TYPES:
                    info=TOWER_TYPES[label]
                    if label=="Farm": tooltip_lines=[f"Income per Wave: ${info['income']}",f"Cost: ${info['cost']}"]
                    elif label=="Missile": tooltip_lines=[f"Global Range",f"Damage: {info['damage']}",f"Rate: {round(FPS/info['cooldown'],2)} /s",f"Cost: ${info['cost']}"]
                    else: tooltip_lines=[f"Range: {info['range']}",f"Damage: {info['damage']}",f"Rate: {round(FPS/info['cooldown'],2)} /s",f"Cost: ${info['cost']}"]
                if info:
                    tooltip_x,tooltip_y=rect.x-170,rect.y
                    pygame.draw.rect(win,BLACK,(tooltip_x,tooltip_y,160,70)); pygame.draw.rect(win,WHITE,(tooltip_x,tooltip_y,160,70),2)
                    for j,text in enumerate(tooltip_lines):
                        win.blit(font.render(text,True,WHITE),(tooltip_x+5,tooltip_y+5+j*15))
        return button_rects
    
    def draw_map_selection_screen(win,font,mx,my):
        win.fill(BLACK)
        gridfall_font,subtitle_font,option_font=pygame.font.SysFont("Arial",70,bold=True),pygame.font.SysFont("Arial",40),pygame.font.SysFont("Arial",30)
        title_text=gridfall_font.render("Gridfall",True,YELLOW)
        win.blit(title_text,(NATIVE_WIDTH//2-title_text.get_width()//2,80))
        subtitle_text=subtitle_font.render("Select a Map",True,WHITE)
        win.blit(subtitle_text,(NATIVE_WIDTH//2-subtitle_text.get_width()//2,160))
        map_buttons=[]
        for i,map_name in enumerate(MAPS.keys()):
            rect=pygame.Rect(NATIVE_WIDTH//2-150,220+i*70,300,60)
            map_buttons.append({"label":map_name,"rect":rect})
            pygame.draw.rect(win,GRAY,rect); pygame.draw.rect(win,WHITE,rect,3)
            label=option_font.render(map_name,True,WHITE)
            win.blit(label,(rect.x+(rect.width-label.get_width())//2,rect.y+15))
            
            if rect.collidepoint(mx,my):
                info=MAPS[map_name]
                tooltip_x,tooltip_y,tooltip_width,tooltip_height=rect.x-320,rect.y-20,300,220 
                if tooltip_x < 0: tooltip_x = rect.x + 310 
    
                pygame.draw.rect(win,BLACK,(tooltip_x,tooltip_y,tooltip_width,tooltip_height)); pygame.draw.rect(win,WHITE,(tooltip_x,tooltip_y,tooltip_width,tooltip_height),2)
                preview_rect=pygame.Rect(tooltip_x+10,tooltip_y+10,tooltip_width-20,120)
                pygame.draw.rect(win,(20,20,20),preview_rect)
                
    
                map_grid = info.get("grid")
                if map_grid:
                    num_rows = len(map_grid)
                    num_cols = len(map_grid[0])
                    
    
                    tile_w = preview_rect.width / num_cols
                    tile_h = preview_rect.height / num_rows
    
                    for r in range(num_rows):
                        for c in range(num_cols):
                            if map_grid[r][c] == 1:
                                tile_rect = pygame.Rect(
                                    preview_rect.left + c * tile_w,
                                    preview_rect.top + r * tile_h,
                                    math.ceil(tile_w),
                                    math.ceil(tile_h)
                                )
                                pygame.draw.rect(win, YELLOW, tile_rect)
    
    
                difficulty_text=font.render(f"Difficulty: {info['difficulty']}",True,YELLOW)
                win.blit(difficulty_text,(tooltip_x+10,tooltip_y+140))
                desc_rect=pygame.Rect(tooltip_x+10,tooltip_y+170,tooltip_width-20,tooltip_height-180)
                draw_text_wrapped(win,info['description'],WHITE,desc_rect,font)
    
        load_button_rect,quit_button_rect=pygame.Rect(NATIVE_WIDTH//2-260,NATIVE_HEIGHT-100,200,50),pygame.Rect(NATIVE_WIDTH//2+60,NATIVE_HEIGHT-100,200,50)
        pygame.draw.rect(win,GREEN,load_button_rect); pygame.draw.rect(win,RED,quit_button_rect)
        win.blit(option_font.render("Load Game",True,WHITE),(load_button_rect.x+35,load_button_rect.y+10))
        win.blit(option_font.render("Quit",True,WHITE),(quit_button_rect.x+70,quit_button_rect.y+10))
        return map_buttons,load_button_rect,quit_button_rect
    def generate_wave(wave):
        power=wave*10
        queue=[]
        while power>0:
            available_enemies = [e for e in enemy_types if e.cost <= power]
            if not available_enemies: break
            enemy = random.choice(available_enemies)
            queue.append(enemy)
            power -= enemy.cost
        return queue
    
    pause_buttons=[
        {"label":"Continue","action":"continue"},{"label":"Codex","action":"codex"},
        {"label":"Save Game","action":"save"},{"label":"Load Game","action":"load"},
        {"label":"Restart","action":"restart"},{"label":"Minimize","action":"minimize"},
        {"label":"Quit","action":"quit"},
    ]
    
    def draw_pause_menu(win):
        overlay=pygame.Surface((NATIVE_WIDTH,NATIVE_HEIGHT),pygame.SRCALPHA)
        overlay.fill((0,0,0,180)); win.blit(overlay,(0,0))
        menu_font=pygame.font.SysFont("Arial",30)
        for i,btn in enumerate(pause_buttons):
            rect=pygame.Rect(NATIVE_WIDTH//2-100,100+i*70,200,50)
            pygame.draw.rect(win,GRAY,rect); pygame.draw.rect(win,WHITE,rect,3)
            label=menu_font.render(btn["label"],True,WHITE)
            win.blit(label,(rect.x+(rect.width-label.get_width())//2,rect.y+10))
            btn["rect"]=rect
    
    def save_game(file_path="savegame.json"):
        if wave_active: return
        towers_data=[]
        for tower in towers:
            tower_info={"kind":tower.kind,"x":tower.x,"y":tower.y,"level":tower.level,"total_cost":tower.total_cost,"damage_done":tower.damage_done,"damage_points":tower.damage_points,"damage_upgrade_cost":tower.damage_upgrade_cost,"firerate_upgrade_cost":tower.firerate_upgrade_cost,"range_upgrade_cost":tower.range_upgrade_cost,"damage":tower.damage,"range":tower.range,"cooldown":tower.cooldown}
            if hasattr(tower,'income'): tower_info['income']=tower.income
            towers_data.append(tower_info)
        current_map_name=None
        for name,map_data in MAPS.items():
            if map_data["path"]==PATH: current_map_name=name; break
        game_state_={"wave":wave,"money":money,"player_health":player_health,"towers":towers_data,"map_name":current_map_name,"discovered":list(discovered_enemies)}
        with open(file_path,'w') as f: json.dump(game_state_,f,indent=4)
        print("Game Saved!")
    
    def load_game(file_path="savegame.json"):
        global wave,money,player_health,towers,bullets,enemies,spawn_queue,wave_active,PATH,discovered_enemies,upgrade_message,upgrade_message_timer
        try:
            with open(file_path,'r') as f: game_state_=json.load(f)
            wave,money,player_health=game_state_["wave"],game_state_["money"],game_state_["player_health"]
            towers.clear();enemies.clear();bullets.clear();spawn_queue.clear();wave_active=False
            map_name=game_state_.get("map_name")
            if map_name and map_name in MAPS: PATH=MAPS[map_name]["path"]
            else: PATH=list(MAPS.values())[0]["path"]
            if PATH: Enemy.x,Enemy.y=PATH[0]
            discovered_list=game_state_.get("discovered",[])
            discovered_enemies=set(discovered_list)
            for tower_data in game_state_["towers"]:
                kind,x,y,level=tower_data["kind"],tower_data["x"],tower_data["y"],tower_data["level"]
                new_tower = None
                tower_class_map = {
                    "Poison": PoisonTower, "Electric": ElectricTower, "Frost": FrostTower,
                    "Vampire": VampireTower, "Farm": FarmTower
                }
                if kind in tower_class_map:
                    new_tower = tower_class_map[kind](x, y, level=level)
                elif kind in TOWER_TYPES:
                    info = TOWER_TYPES[kind]
                    new_tower = Tower(x,y,info["color"],info["cooldown"],info["damage"],info["range"],kind=kind,level=level)
    
                if new_tower:
                    new_tower.total_cost,new_tower.damage_done,new_tower.damage_points=tower_data["total_cost"],tower_data["damage_done"],tower_data["damage_points"]
                    new_tower.damage_upgrade_cost,new_tower.firerate_upgrade_cost,new_tower.range_upgrade_cost=tower_data["damage_upgrade_cost"],tower_data["firerate_upgrade_cost"],tower_data["range_upgrade_cost"]
                    new_tower.damage,new_tower.range,new_tower.cooldown=tower_data.get('damage',new_tower.damage),tower_data.get('range',new_tower.range),tower_data.get('cooldown',new_tower.cooldown)
                    if new_tower.kind=="Farm": new_tower.income=tower_data.get('income',new_tower.income)
                    towers.append(new_tower)
            print("Game Loaded!"); return True
        except FileNotFoundError: upgrade_message,upgrade_message_timer="No save file found.",FPS*2; return False
        except (KeyError, json.JSONDecodeError) as e: upgrade_message,upgrade_message_timer=f"Save file corrupted: {e}",FPS*3; return False
    
    def draw_text_wrapped(surface,text,color,rect,font,aa=False,bkg=None):
        rect=pygame.Rect(rect); y,lineSpacing,fontHeight=rect.top,-2,font.size("Tg")[1]
        while text:
            i=1
            if y+fontHeight>rect.bottom: break
            while font.size(text[:i])[0]<rect.width and i<len(text): i+=1
            if i<len(text): i=text.rfind(" ",0,i)+1
            if bkg: image=font.render(text[:i],1,color,bkg); image.set_colorkey(bkg)
            else: image=font.render(text[:i],aa,color)
            surface.blit(image,(rect.left,y)); y+=fontHeight+lineSpacing; text=text[i:]
        return text
    
    def draw_codex_screen(win,font):
        global codex_mode,codex_selected_item
        pygame.draw.rect(win,(20,20,40),(50,50,NATIVE_WIDTH-100,NATIVE_HEIGHT-100)); pygame.draw.rect(win,WHITE,(50,50,NATIVE_WIDTH-100,NATIVE_HEIGHT-100),3)
        tower_tab_rect,enemy_tab_rect,ability_tab_rect=pygame.Rect(60,60,100,40),pygame.Rect(170,60,100,40),pygame.Rect(280,60,100,40)
        pygame.draw.rect(win,(40,40,60) if codex_mode=="Towers" else GRAY,tower_tab_rect); pygame.draw.rect(win,(40,40,60) if codex_mode=="Enemies" else GRAY,enemy_tab_rect); pygame.draw.rect(win,(40,40,60) if codex_mode=="Abilities" else GRAY,ability_tab_rect)
        win.blit(font.render("Towers",True,WHITE),(75,70)); win.blit(font.render("Enemies",True,WHITE),(180,70)); win.blit(font.render("Abilities",True,WHITE),(290,70))
        back_button_rect=pygame.Rect(NATIVE_WIDTH-160,60,100,40)
        pygame.draw.rect(win,RED,back_button_rect); win.blit(font.render("Back",True,WHITE),(NATIVE_WIDTH-135,70))
        pygame.draw.rect(win,(30,30,50),(60,110,300,NATIVE_HEIGHT-170)); pygame.draw.rect(win,(30,30,50),(370,110,NATIVE_WIDTH-430,NATIVE_HEIGHT-170))
        list_items=[]
        if codex_mode=="Towers": items_to_draw=TOWER_TYPES.items()
        elif codex_mode=="Enemies": items_to_draw=[(e.name,e) for e in enemy_types]
        else: items_to_draw=PLAYER_ABILITIES.items()
        for i,(name,data) in enumerate(items_to_draw):
            item_rect=pygame.Rect(70,120+i*30,280,25)
            is_discovered=name in discovered_enemies if codex_mode=="Enemies" else True
            list_items.append({"name":name,"rect":item_rect,"data":data,"discovered":is_discovered})
            is_selected=codex_selected_item and codex_selected_item["name"]==name
            display_name,color=(name,YELLOW) if is_discovered else ("???",YELLOW if is_selected else GRAY)
            win.blit(font.render(display_name,True,color),(75,122+i*30))
        if codex_selected_item:
            data,name,is_discovered=codex_selected_item["data"],codex_selected_item["name"],codex_selected_item["discovered"]
            title_font=pygame.font.SysFont("Arial",30)
            display_name=name if is_discovered else "???"
            win.blit(title_font.render(display_name,True,YELLOW),(380,120))
            desc_rect=pygame.Rect(380,160,NATIVE_WIDTH-450,100)
            if is_discovered:
                description = ""
                if codex_mode=="Towers": description=data["description"]
                elif codex_mode=="Enemies": description=data.description
                else: description=data["description"]
                draw_text_wrapped(win,description,WHITE,desc_rect,font)
                y_offset,stats=280,[]
                if codex_mode=="Towers":
                    stats.append(f"Cost: ${data['cost']}")
                    if data['damage']>0: stats.append(f"Damage: {data['damage']}")
                    if data['range']>0: stats.append(f"Range: {data['range']}")
                    if data['cooldown']>0: stats.append(f"Fire Rate: {round(FPS/data['cooldown'],2)}/s")
                    if data.get('income',0)>0: stats.append(f"Income per Wave: ${data['income']}")
                elif codex_mode=="Enemies": stats=[f"Health: {data.health}",f"Speed: {data.speed}",f"Reward: ${data.reward}"]
                else: stats=[f"Cost: ${data['cost']}",f"Cooldown: {data['cooldown']//FPS} seconds"]
                for stat in stats:
                    win.blit(font.render(stat,True,WHITE),(380,y_offset)); y_offset+=25
            else:
                draw_text_wrapped(win,"Encounter this unit in battle to unlock its data.",WHITE,desc_rect,font)
        return tower_tab_rect,enemy_tab_rect,ability_tab_rect,back_button_rect,list_items
    WIN = display
    clock = pygame.time.Clock()
    run = True
    
     
    enemies,towers,bullets = [],[],[]
    spawn_timer,spawn_interval = 0,30
    wave,money,player_health = 1,1000,10
    wave_active,is_paused,showing_advanced_menu,restart_requested = False,False,False,False
    selected_tower_type,selected_tower = None,None
    camera_zoom = 1.0
    hovered_button = -1
    game_state,codex_mode,codex_selected_item = "map_selection","Towers",None
    discovered_enemies = set()
    current_map_grid = None
    current_map_data = None
    PATH = []
    
    PLAYER_ABILITIES = {
        "Airstrike":{"cost":500,"cooldown":60*FPS,"description":"Calls down a powerful, high-damage explosion on a target area."},
        "Global Freeze":{"cost":250,"cooldown":45*FPS,"description":"Instantly freezes all enemies on the screen for 3 seconds."},
        "Overcharge":{"cost":400,"cooldown":90*FPS,"duration":10*FPS,"description":"Doubles the attack speed of all towers for a short duration."}
    }
    upgrade_message_timer = 0
    airstrike_cooldown,global_freeze_cooldown,overcharge_cooldown = 0,0,0
    overcharge_active_timer,showing_abilities_menu,targeting_mode = 0,False,None
    
    TOWER_TYPES = {
        "Normal":{"color":GREEN,"cooldown":FPS/2,"damage":1,"cost":50,"range":150,"description":"A standard, reliable tower. Effective in numbers.","barrel":{"width":6,"height":18}},
        "Machine Gun":{"color":BLUE,"cooldown":FPS/7.5,"damage":0.5,"cost":250,"range":150,"description":"Boasts an exceptionally high fire rate, overwhelming enemies with a constant stream of bullets.","barrel":{"width":4,"height":20}},
        "Cannon":{"color":RED,"cooldown":FPS,"damage":4,"cost":150,"range":200,"description":"Fires slow, high-damage shots. Excellent for taking down tougher, single targets.","barrel":{"width":10,"height":16}},
        "Missile":{"color":PURPLE,"cooldown":FPS*2,"damage":10,"cost":500,"range":9999,"description":"Has unlimited range, capable of hitting any enemy on the map. (No splash damage).","barrel":{"width":8,"height":18}},
        "Flame":{"color":ORANGE,"cooldown":FPS/20,"damage":0.125,"cost":400,"range":100,"description":"Continuously damages all enemies within its short range. Great for crowd control.","barrel":{"width":12,"height":12}},
        "Poison":{"color":(0,150,0),"cooldown":FPS/2,"damage":0,"cost":350,"range":150,"description":"Applies a damage-over-time effect to enemies, draining their health after the initial hit.","barrel":{"width":5,"height":16}},
        "Electric":{"color":(100,100,255),"cooldown":FPS/2,"damage":1,"cost":400,"range":150,"description":"Has a chance to briefly stun enemies, halting their advance.","barrel":{"width":3,"height":22}},
        "Frost":{"color":(150,255,255),"cooldown":FPS,"damage":0.5,"cost":300,"range":130,"description":"Slows down all enemies within its radius, making them easier targets for other towers.","barrel":{"width":14,"height":14}},
        "Vampire":{"color":(128,0,128),"cooldown":FPS,"damage":1,"cost":500,"range":150,"description":"Heals the player for a portion of the damage it deals.","barrel":{"width":6,"height":18}},
        "Farm":{"color":(255,215,0),"cooldown":FPS*5,"damage":0,"cost":600,"range":0,"income":15,"description":"Generates extra money at the end of each wave, boosting your economy."},
    }
    
    if sounds_loaded: pygame.mixer.music.play(-1)
    
    while run:
        clock.tick(FPS)
        mx_raw,my_raw = pygame.mouse.get_pos()
        screen_width,screen_height = screen.get_size()
        scale = min(screen_width/NATIVE_WIDTH,screen_height/NATIVE_HEIGHT) if NATIVE_WIDTH > 0 and NATIVE_HEIGHT > 0 else 1
        offset_x = (screen_width-NATIVE_WIDTH*scale)/2
        offset_y = (screen_height-NATIVE_HEIGHT*scale)/2
        mx,my = int((mx_raw-offset_x)/scale), int((my_raw-offset_y)/scale)
        if mx<0 or my<0 or mx>NATIVE_WIDTH or my>NATIVE_HEIGHT: mx,my=-1,-1
                        
        if game_state == "map_selection":
            map_buttons,load_button,quit_button = draw_map_selection_screen(WIN,font,mx,my)
            for event in pygame.event.get():
                if event.type==pygame.QUIT: run=False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: run = False
                elif event.type==pygame.MOUSEBUTTONDOWN:
                    if load_button.collidepoint(mx,my):
                        if load_game(): game_state="playing"
                    elif quit_button.collidepoint(mx,my): run=False
                    else:
                        for btn in map_buttons:
                            if btn["rect"].collidepoint(mx,my):
                                current_map_data = MAPS[btn["label"]]
                                current_map_grid = current_map_data["grid"]
                                game_state="playing"
            scaled_display = pygame.transform.smoothscale(WIN, (int(NATIVE_WIDTH*scale),int(NATIVE_HEIGHT*scale)))
            screen.fill(BLACK); screen.blit(scaled_display,(int(offset_x),int(offset_y))); pygame.display.update()
            continue
    
        elif game_state == "codex":
            tower_tab,enemy_tab,ability_tab,back_btn,list_items = draw_codex_screen(WIN,font)
            for event in pygame.event.get():
                if event.type==pygame.QUIT: run=False
                elif event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE: game_state,is_paused="playing",True
                elif event.type==pygame.MOUSEBUTTONDOWN:
                    if back_btn.collidepoint(mx,my): game_state,is_paused="playing",True
                    elif tower_tab.collidepoint(mx,my): codex_mode,codex_selected_item="Towers",None
                    elif enemy_tab.collidepoint(mx,my): codex_mode,codex_selected_item="Enemies",None
                    elif ability_tab.collidepoint(mx,my): codex_mode,codex_selected_item="Abilities",None
                    else:
                        for item in list_items:
                            if item["rect"].collidepoint(mx,my): codex_selected_item=item; break
            scaled_display = pygame.transform.smoothscale(WIN, (int(NATIVE_WIDTH*scale),int(NATIVE_HEIGHT*scale)))
            screen.fill(BLACK); screen.blit(scaled_display,(int(offset_x),int(offset_y))); pygame.display.update()
            continue
    
        elif game_state == "playing":
            horizon_y_val = NATIVE_HEIGHT * 0.4
            
            OLD_PATH = list(PATH) if PATH else []
            PATH = generate_path_from_grid(current_map_data)
            
            for tower in towers:
                tower.x, tower.y = get_screen_coords_for_grid_cell(tower.grid_r, tower.grid_c, horizon_y_val, NATIVE_WIDTH, NATIVE_HEIGHT, GRID_ROWS, GRID_COLS, camera_zoom)
    
            if OLD_PATH and len(OLD_PATH) > 1 and PATH:
                for enemy in enemies:
                    if enemy.path_index < len(OLD_PATH) - 1 and enemy.path_index < len(PATH) - 1:
                        start = OLD_PATH[enemy.path_index]
                        end = OLD_PATH[enemy.path_index + 1]
                        segment_vec = (end[0] - start[0], end[1] - start[1])
                        enemy_vec = (enemy.x - start[0], enemy.y - start[1])
                        segment_len_sq = segment_vec[0]**2 + segment_vec[1]**2
                        progress = 0.0
                        if segment_len_sq > 0:
                            progress = (enemy_vec[0] * segment_vec[0] + enemy_vec[1] * segment_vec[1]) / segment_len_sq
                            progress = max(0, min(1, progress))
                        new_start = PATH[enemy.path_index]
                        new_end = PATH[enemy.path_index + 1]
                        enemy.x = new_start[0] + (new_end[0] - new_start[0]) * progress
                        enemy.y = new_start[1] + (new_end[1] - new_start[1]) * progress
            elif not OLD_PATH and PATH: # Initialize position for the very first frame
                 for enemy in enemies:
                    enemy.x, enemy.y = PATH[0]
    
            draw_background_and_path(WIN, (20,40,70), horizon_y_val, current_map_grid)
            
            if not is_paused:
                if airstrike_cooldown>0: airstrike_cooldown-=1
                if global_freeze_cooldown>0: global_freeze_cooldown-=1
                if overcharge_cooldown>0: overcharge_cooldown-=1
                if overcharge_active_timer>0:
                    overcharge_active_timer-=1
                    if overcharge_active_timer==0:
                        for tower in towers: tower.is_overcharged=False
                
                newly_spawned_from_bosses=[]
                for enemy in enemies[:]:
                    spawned_this_frame = enemy.move(wave)
                    if spawned_this_frame: newly_spawned_from_bosses.extend(spawned_this_frame)
                    
                    if enemy.path_index >= len(PATH) -1:
                        player_health-=round(enemy.health)
                        if enemy in enemies: enemies.remove(enemy)
                    elif enemy.health<=0:
                        if sounds_loaded: death_sound.play()
                        money+=enemy.reward
                        death_effects.append({"x":enemy.x,"y":enemy.y,"radius":5,"max_radius":20,"color":enemy.color,"life":40,"stage":"growing"})
                        if enemy in enemies: enemies.remove(enemy)
                if newly_spawned_from_bosses: enemies.extend(newly_spawned_from_bosses)
                
                if wave_active and spawn_queue:
                    spawn_timer-=1
                    if spawn_timer<=0:
                        e=spawn_queue.pop(0)
                        discovered_enemies.add(e.name)
                        enemies.append(Enemy(e.health*(1.2**(wave-1)), e.speed,e.color,e.reward,e.size,e))
                        spawn_timer=spawn_interval
                elif wave_active and not spawn_queue and not enemies:
                    wave_active,wave,money=False,wave+1,money+(100*wave)
                    for tower in towers:
                        if tower.kind=="Farm":
                            money+=tower.income
                            floating_texts.append({"x":tower.x,"y":tower.y,"text":f"+${tower.income}","life":60,"alpha":255})
                
                for tower in towers: tower.shoot(enemies,bullets)
                
                for bullet in bullets[:]:
                    bullet.move()
                    if bullet.target and math.hypot(bullet.x-bullet.target.x,bullet.y-bullet.target.y)<10:
                        if sounds_loaded: hit_sound.play()
                        for _ in range(5): particles.append({"x":bullet.x,"y":bullet.y,"vx":random.uniform(-1.5,1.5),"vy":random.uniform(-1.5,1.5),"radius":random.randint(2,4),"color":(255,200,0),"life":20})
                        
                        if hasattr(bullet.tower, 'kind') and bullet.tower.kind in ["Cannon", "Missile"]:
                             death_effects.append({"x":bullet.target.x, "y":bullet.target.y, "radius":10, "max_radius":60, "color":ORANGE, "life":40, "stage":"growing"})
                        
                        if hasattr(bullet.tower, 'kind') and bullet.tower.kind == "Electric":
                            chain_radius = 90; max_chains = 2; chained_enemies = 0
                            for other_enemy in enemies:
                                if other_enemy is not bullet.target and chained_enemies < max_chains:
                                    if math.hypot(bullet.target.x - other_enemy.x, bullet.target.y - other_enemy.y) < chain_radius:
                                        lightning_effects.append({"start": (bullet.target.x, bullet.target.y),"end": (other_enemy.x, other_enemy.y),"life": 10})
                                        other_enemy.health -= bullet.damage * 0.5 
                                        chained_enemies += 1
    
                        if not isinstance(bullet,VampireBullet):
                            damage_to_deal=bullet.damage
                            if bullet.target.ability=="armor": damage_to_deal=max(0.1,bullet.damage-1)
                            bullet.target.health-=damage_to_deal
                            floating_texts.append({"x":bullet.target.x,"y":bullet.target.y,"text":f"-{round(bullet.damage,1)}","life":40,"alpha":255})
                            if hasattr(bullet,'tower') and bullet.tower: bullet.tower.damage_done+=bullet.damage; bullet.tower.damage_points+=bullet.damage
                            if bullet in bullets: bullets.remove(bullet)
            
            objects_to_draw = sorted(towers + enemies, key=lambda obj: obj.y)
            for obj in objects_to_draw: obj.draw(WIN)
            
            for bullet in bullets: bullet.draw(WIN)
            
            for p in particles[:]:
                pygame.draw.circle(WIN,p["color"],(int(p["x"]),int(p["y"])),int(p["radius"])); p["x"]+=p["vx"]; p["y"]+=p["vy"]; p["radius"]*=0.9; p["life"]-=1
                if p["life"]<=0 or p["radius"]<0.5: particles.remove(p)
    
            for bolt in lightning_effects[:]:
                mid_x = bolt["start"][0] + (bolt["end"][0] - bolt["start"][0]) / 2 + random.uniform(-8, 8)
                mid_y = bolt["start"][1] + (bolt["end"][1] - bolt["start"][1]) / 2 + random.uniform(-8, 8)
                points = [bolt["start"], (mid_x, mid_y), bolt["end"]]
                pygame.draw.lines(WIN, (200, 220, 255), False, points, 2)
                bolt["life"] -= 1
                if bolt["life"] <= 0: lightning_effects.remove(bolt)
            
            for nova in nova_effects[:]:
                progress = 1 - (nova['life'] / 25.0); current_radius = int(nova['max_radius'] * progress); alpha = int(255 * (nova['life'] / 25.0))
                if current_radius > 0:
                    surf = pygame.Surface((current_radius*2, current_radius*2), pygame.SRCALPHA)
                    pygame.draw.circle(surf, (150, 220, 255, alpha), (current_radius, current_radius), current_radius, 3)
                    WIN.blit(surf, (nova['x'] - current_radius, nova['y'] - current_radius))
                nova['life'] -= 1
                if nova['life'] <= 0: nova_effects.remove(nova)
    
            for ft in floating_texts[:]:
                ft["y"]-=0.5; ft["life"]-=1; ft["alpha"]=max(0,int(255*(ft["life"]/40))); color = ft.get("color", (255, 0, 0))
                text_surf=font.render(ft["text"],True, color); text_surf.set_alpha(ft["alpha"]); WIN.blit(text_surf,(ft["x"],ft["y"]))
                if ft["life"]<=0: floating_texts.remove(ft)
    
            for e in death_effects[:]:
                alpha,effect_radius=int(255*(e["life"]/40)),int(e["radius"]); surf=pygame.Surface((effect_radius*2,effect_radius*2),pygame.SRCALPHA)
                pygame.draw.circle(surf,(*e["color"],alpha),(effect_radius,effect_radius),effect_radius); WIN.blit(surf,(int(e["x"]-effect_radius),int(e["y"]-effect_radius)))
                if e["stage"]=="growing":
                    e["radius"]+=max(0.5,(e["max_radius"]-e["radius"])*0.2)
                    if e["radius"]>=e["max_radius"]-0.5: e["stage"]="shrinking"
                elif e["stage"]=="shrinking":
                    e["radius"]-=max(0.8,e["radius"]*0.1)
                    if e["radius"]<=0.5: e["life"]=0
                e["life"]-=1
                if e["life"]<=0: death_effects.remove(e)
    
            WIN.blit(font.render(f"Money: {money}",True,WHITE),(10,10)); WIN.blit(font.render(f"Wave: {wave}",True,WHITE),(10,40)); WIN.blit(font.render(f"Health: {player_health:.1f}",True,WHITE),(10,70))
            
            if selected_tower:
                y_ratio = max(0, min(1, (selected_tower.y - horizon_y_val) / (NATIVE_HEIGHT - horizon_y_val)))
                grid_depth_ratio = y_ratio ** (camera_zoom / 2.0)
                scale_factor = 0.3 + grid_depth_ratio * 0.7
                if selected_tower.range > 0 and selected_tower.kind != "Missile":
                    ellipse_width = int(selected_tower.range * scale_factor * 2); ellipse_height = int(selected_tower.range * scale_factor * scale_factor * 2)
                    if ellipse_width > 0 and ellipse_height > 0:
                        range_surf = pygame.Surface((ellipse_width, ellipse_height), pygame.SRCALPHA)
                        pygame.draw.ellipse(range_surf, (0, 100, 255, 70), range_surf.get_rect(), 3)
                        WIN.blit(range_surf, (selected_tower.x - ellipse_width // 2, selected_tower.y - ellipse_height // 2))
                
                y_offset=200
                lines=[f"Type: {selected_tower.kind}", f"Targeting: {selected_tower.targeting_mode}", f"Level: {selected_tower.level}",f"Total Spent: {selected_tower.total_cost}",f"Damage Done: {selected_tower.damage_done:.1f}",f"Damage: {selected_tower.damage}",f"Fire Rate: {FPS/selected_tower.cooldown:.2f}/s",f"Range: {selected_tower.range}",f"Damage Points: {int(selected_tower.damage_points)}",f"Damage Upgrade Cost: {selected_tower.damage_upgrade_cost}",f"Firing Rate Upgrade Cost: {selected_tower.firerate_upgrade_cost}",f"Range Upgrade Cost: {selected_tower.range_upgrade_cost}"]
                for i, line in enumerate(lines):
                    WIN.blit(font.render(line,True,WHITE),(10,y_offset + i*20))
            
            if upgrade_message_timer>0:
                upgrade_message_timer-=1
                msg_surface=font.render(upgrade_message,True,(255,0,0)); WIN.blit(msg_surface,(10,HEIGHT-40))
    
            if selected_tower: menu_labels = MENU_SETS["tower_selected"]
            elif showing_abilities_menu: menu_labels = MENU_SETS["abilities"]
            elif showing_advanced_menu: menu_labels = MENU_SETS["advanced"]
            else: menu_labels = MENU_SETS["default"]
            
            hovered_button = -1
            button_rects_on_screen = []
            for i,label in enumerate(menu_labels):
                rect = pygame.Rect(810, 10+i*50, 180, 45)
                button_rects_on_screen.append((label, rect))
                if rect.collidepoint(mx,my): hovered_button = i
            draw_menu(WIN,font,hovered_button,menu_labels)
            
            if selected_tower_type and mx<800:
                snapped_pos = snap_to_3d_grid(mx, my, horizon_y_val, NATIVE_WIDTH, NATIVE_HEIGHT, GRID_ROWS, GRID_COLS, camera_zoom)
                if snapped_pos:
                    grid_x, grid_y = snapped_pos
                    y_ratio = max(0, min(1, (grid_y - horizon_y_val) / (NATIVE_HEIGHT - horizon_y_val)))
                    grid_depth_ratio = y_ratio ** (camera_zoom / 2.0)
                    scale_factor = 0.3 + grid_depth_ratio * 0.7
                    if selected_tower_type.range > 0 and selected_tower_type.kind != "Missile":
                        ellipse_width = int(selected_tower_type.range * scale_factor * 2); ellipse_height = int(selected_tower_type.range * scale_factor * scale_factor * 2)
                        if ellipse_width > 0 and ellipse_height > 0:
                            range_surf = pygame.Surface((ellipse_width, ellipse_height), pygame.SRCALPHA)
                            pygame.draw.ellipse(range_surf, (0, 100, 255, 70), range_surf.get_rect(), 3)
                            WIN.blit(range_surf, (grid_x - ellipse_width // 2, grid_y - ellipse_height // 2))
                    scaled_width=int(selected_tower_type.base_image.get_width()*scale_factor); scaled_height=int(selected_tower_type.base_image.get_height()*scale_factor)
                    if scaled_width>0 and scaled_height>0:
                        scaled_base=pygame.transform.smoothscale(selected_tower_type.base_image,(scaled_width,scaled_height)); base_rect=scaled_base.get_rect(center=(grid_x,grid_y)); WIN.blit(scaled_base,base_rect)
                    if selected_tower_type.barrel_image:
                        scaled_barrel_w=int(selected_tower_type.barrel_image.get_width()*scale_factor); scaled_barrel_h=int(selected_tower_type.barrel_image.get_height()*scale_factor)
                        if scaled_barrel_w>0 and scaled_barrel_h>0:
                            scaled_barrel=pygame.transform.smoothscale(selected_tower_type.barrel_image,(scaled_barrel_w,scaled_barrel_h)); barrel_rect=scaled_barrel.get_rect(center=(grid_x,grid_y)); WIN.blit(scaled_barrel,barrel_rect)
                    if selected_tower_type.kind=="Missile": WIN.blit(font.render("Global Range",True,YELLOW),(grid_x+20,grid_y-10))
            
            if is_paused: draw_pause_menu(WIN)
    
            for event in pygame.event.get():
                if event.type==pygame.QUIT: run=False
                elif event.type==pygame.KEYDOWN and event.key==pygame.K_ESCAPE: is_paused = not is_paused
                elif event.type==pygame.MOUSEBUTTONDOWN:
                    if is_paused:
                        for btn in pause_buttons:
                            if "rect" in btn and btn["rect"].collidepoint(mx,my):
                                if btn["action"]=="continue": is_paused=False
                                elif btn["action"]=="codex": game_state,codex_selected_item,is_paused="codex",None,True
                                elif btn["action"]=="save": save_game(); is_paused=False
                                elif btn["action"]=="load":
                                    if load_game(): is_paused=False
                                elif btn["action"]=="quit": run=False
                                elif btn["action"]=="minimize": pygame.display.iconify()
                                elif btn["action"]=="restart": restart_requested,is_paused=True,False
                        continue
                    
                    if mx>800:
                        if hovered_button!=-1:
                            if sounds_loaded: click_sound.play()
                            button_label = button_rects_on_screen[hovered_button][0]
                            if button_label=="Upgrade":
                                if selected_tower and selected_tower.level<5:
                                    cost=100*selected_tower.level
                                    if money>=cost: money-=cost; selected_tower.upgrade()
                            elif button_label=="Sell":
                                if selected_tower: money+=int(selected_tower.total_cost*0.5); towers.remove(selected_tower); selected_tower=None
                            elif button_label=="Relocate":
                                if selected_tower: pass
                            elif button_label=="Next Wave":
                                if not wave_active: wave_active,spawn_queue=True,generate_wave(wave)
                            elif button_label=="Cancel":
                                selected_tower,selected_tower_type,targeting_mode=None,None,None
                            elif button_label in TOWER_TYPES:
                                info=TOWER_TYPES[button_label]
                                tower_class={"Poison":PoisonTower,"Electric":ElectricTower,"Frost":FrostTower,"Vampire":VampireTower,"Farm":FarmTower}.get(button_label,Tower)
                                if tower_class!=Tower: selected_tower_type=tower_class(0,0,level=1)
                                else: selected_tower_type=Tower(0,0,info["color"],info["cooldown"],info["damage"],info["range"],kind=button_label)
                                selected_tower_type.cost,selected_tower_type.total_cost,selected_tower=info["cost"],info["cost"],None
                            elif button_label=="Advanced Towers": showing_advanced_menu,showing_abilities_menu=True,False
                            elif button_label=="Abilities": showing_abilities_menu,showing_advanced_menu=True,False
                            elif button_label=="Back": showing_advanced_menu,showing_abilities_menu=False,False
                    else: 
                        clicked_tower=None
                        for tower in towers:
                            if math.hypot(tower.x-mx,tower.y-my)<20: clicked_tower=tower; break
                        
                        if clicked_tower: selected_tower,selected_tower_type=clicked_tower,None
                        elif selected_tower_type:
                            grid_indices = get_grid_indices_from_pos(mx, my, horizon_y_val, NATIVE_WIDTH, NATIVE_HEIGHT, GRID_ROWS, GRID_COLS, camera_zoom)
                            if grid_indices:
                                r, c = grid_indices
                                can_build = (current_map_grid[r][c] == 0)
                                is_spot_occupied = any(t.grid_r == r and t.grid_c == c for t in towers)
                                if not can_build or is_spot_occupied:
                                    message = "Cannot place tower on the path!" if not can_build else "Cannot place tower here!"
                                    upgrade_message,upgrade_message_timer,selected_tower_type = message, FPS*2, None
                                elif money>=selected_tower_type.cost:
                                    money-=selected_tower_type.cost
                                    kind=selected_tower_type.kind; level=selected_tower_type.level
                                    if kind=="Poison": new_tower=PoisonTower(r,c,level=level)
                                    elif kind=="Electric": new_tower=ElectricTower(r,c,level=level)
                                    elif kind=="Frost": new_tower=FrostTower(r,c,level=level)
                                    elif kind=="Vampire": new_tower=VampireTower(r,c,level=level)
                                    elif kind=="Farm": new_tower=FarmTower(r,c,level=level)
                                    else:
                                        info=TOWER_TYPES[kind]
                                        new_tower=Tower(r,c,info["color"],info["cooldown"],info["damage"],info["range"],kind=kind,level=level)
                                    towers.append(new_tower)
                                    selected_tower_type = None
                                else:
                                    upgrade_message,upgrade_message_timer,selected_tower_type="Not enough money!",FPS*2,None
                        else: selected_tower=None
    
            keys = pygame.key.get_pressed()
            zoom_speed = 0.02
            if keys[pygame.K_UP]: camera_zoom += zoom_speed
            if keys[pygame.K_DOWN]: camera_zoom -= zoom_speed
            camera_zoom = max(0.7, min(3.0, camera_zoom))
            
        scaled_display=pygame.transform.smoothscale(WIN,(int(NATIVE_WIDTH*scale),int(NATIVE_HEIGHT*scale)))
        screen.fill(BLACK); screen.blit(scaled_display,(int(offset_x),int(offset_y))); pygame.display.update()
        await asyncio.sleep(0)
    pygame.quit()

asyncio.run(main())