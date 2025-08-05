import pygame
import tkinter as tk
from tkinter import messagebox

import random
import json
import os

# Global variables
current_level = 1
max_levels = 50
player_health = 100
max_health = 100
power_active = False                                 
power_timer = 0
power_duration = 15 * 60  # 15 seconds (60 FPS)
coins_for_power = 5
coins_collected = 0

selected_character = "mario"  # Options: "mario", "doraemon", "heman"

# Save/load progress functions
def save_progress():
    """Save the highest unlocked level to file"""
    try:
        with open('game_progress.json', 'w') as f:
            json.dump({'highest_unlocked_level': current_level}, f)
    except:
        pass  # Silently fail if save fails

def load_progress():
    """Load the highest unlocked level from file"""
    try:
        if os.path.exists('game_progress.json'):
            with open('game_progress.json', 'r') as f:
                data = json.load(f)
                return data.get('highest_unlocked_level', 1)
        else:
            return 1  # Return 1 if no file exists (start with level 1)
    except:
        return 1  # Return 1 on any error

def unlock_next_level():
    """Unlock the next level and save progress"""
    global current_level
    if current_level < max_levels:
        current_level += 1
        save_progress()

# Level selection GUI
def show_level_selection():
    # Load progress
    highest_unlocked = load_progress()
    
    # Create level selection window
    level_window = tk.Toplevel(root)
    level_window.title("Level Selection")
    level_window.geometry("800x600")
    level_window.configure(bg='#2c3e50')
    
    # Title
    title_label = tk.Label(level_window, text="Select Level", font=("Arial", 24, "bold"), 
                          bg='#2c3e50', fg='white')
    title_label.pack(pady=20)
    
    # Create scrollable frame for levels
    canvas = tk.Canvas(level_window, bg='#2c3e50')
    scrollbar = tk.Scrollbar(level_window, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg='#2c3e50')
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Create level buttons in a 10x5 grid for 50 levels
    for i in range(50):
        level_num = i + 1
        row = i // 10
        col = i % 10
        
        # Determine button state
        if level_num <= highest_unlocked:
            # Unlocked level
            button_text = f"Level {level_num}"
            button_bg = '#27ae60'  # Green
            button_fg = 'white'
            command = lambda l=level_num, w=level_window: start_specific_level(l, w)
        else:
            # Locked level
            button_text = f"Level {level_num}\n🔒"
            button_bg = '#95a5a6'  # Gray
            button_fg = 'white'
            command = None
        
        level_button = tk.Button(scrollable_frame, text=button_text, 
                               font=("Arial", 10, "bold"),
                               width=8, height=3,
                               bg=button_bg, fg=button_fg,
                               command=command,
                               relief="raised", bd=3)
        level_button.grid(row=row, column=col, padx=5, pady=5)
    
    # Back to menu button
    back_button = tk.Button(level_window, text="Back to Menu", 
                           font=("Arial", 14, "bold"),
                           bg='#e74c3c', fg='white',
                           command=level_window.destroy,
                           relief="raised", bd=3)
    back_button.pack(pady=20)
    
    # Pack canvas and scrollbar
    canvas.pack(side="left", fill="both", expand=True, padx=20)
    scrollbar.pack(side="right", fill="y")
    
    # Configure canvas scrolling
    level_window.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

def start_specific_level(level, window):
    """Start a specific level"""
    global current_level
    current_level = level
    window.destroy()
    root.destroy()
    run_game()

# Pygame game function
def run_game():
    global current_level, player_health, power_active, power_timer, coins_collected
    
    pygame.init()

    # Set up the display - Fullscreen
    info = pygame.display.Info()
    WIDTH = info.current_w
    HEIGHT = info.current_h
    window = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption(f"Jump Quest - Level {current_level}")

    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GREEN = (0, 255, 0)
    YELLOW = (255, 255, 0)
    RED = (255, 0, 0)
    BLUE = (0, 0, 255)
    ORANGE = (255, 165, 0)
    BROWN = (139, 69, 19)
    LIGHT_BLUE = (135, 206, 235)
    DARK_GREEN = (34, 139, 34)
    PINK = (255, 192, 203)
    LIGHT_GREEN = (144, 238, 144)
    DARK_RED = (139, 0, 0)
    BRIGHT_RED = (255, 50, 50)
    DEEP_RED = (220, 20, 60)
    GOLD = (255, 215, 0)
    DARK_GOLD = (184, 134, 11)
    PURPLE = (128, 0, 128)
    LIGHT_PURPLE = (221, 160, 221)

    # Player properties
    player_width = 40
    player_height = 50
    player_x = 50
    player_y = HEIGHT - player_height - 10
    player_speed = 6  # Balanced speed
    # Calculate jump_height so player can jump from ground to top border
    max_jump_height = (HEIGHT - 20 - player_height) - 20
    jump_height = int((2 * max_jump_height / 0.5) ** 0.5)  # Derived from jump formula
    is_jumping = False
    jump_count = jump_height
    score = 0
    invincible_timer = 0
    on_ground = False
    gravity = 1.0  # Increased gravity for even faster falling speed

    # Reset power-up variables for new level
    power_active = False
    power_timer = 0
    coins_collected = 0

    # Level-specific properties with platforms
    def get_level_properties(level):
        """Generate level properties based on level number"""
        
        # Scale difficulty with level - adjust platforms after level 7
        if level <= 5:
            base_platforms = 3 + (level // 2) + (level // 5)
        elif level <= 7:
            base_platforms = 8 + (level // 2) + (level // 4)
        else:
            base_platforms = 5 + (level // 4)  # Fewer platforms after level 7
        base_coins = 5 + level * 3
        base_obstacles = 2 + level + (level // 3)
        base_enemies = level // 2 + (level // 4)
        base_health_pickups = 2 + (level // 4)
        
        # Smooth background color transition
        def lerp(a, b, t):
            return int(a + (b - a) * t)
        max_levels = 50  # or use the global max_levels if available
        start_color = (135, 206, 235)  # Light blue
        end_color = (10, 10, 20)       # Intense dark
        t = min(1.0, (level - 1) / (max_levels - 1))  # 0.0 at level 1, 1.0 at max level
        background_color = (
            lerp(start_color[0], end_color[0], t),
            lerp(start_color[1], end_color[1], t),
            lerp(start_color[2], end_color[2], t)
        )
        
        # Generate platforms with better distribution to fill right side
        platforms = []
        for i in range(base_platforms):
            if level > 7:
                gap_factor = 6.0  # Even larger space between platforms after level 7
                platform_x = 50 + int(i * (WIDTH - 100) // (base_platforms * gap_factor))
                platform_width = max(40, 120 - level * 7)  # Slightly narrower for more space
            else:
                platform_x = 50 + i * (WIDTH - 100) // base_platforms
                platform_width = max(40, 120 - level * 6)
            platform_height = 20
            
            # Better platform distribution to fill the entire screen width
            if level <= 10:
                # For levels 1-10, use original spacing
                platform_x = 50 + i * (WIDTH - 100) // base_platforms
                platform_y = HEIGHT - 200 - (i * 35) - (level * 10)
            else:
                # For levels 11+, ensure platforms cover the full width and don't go off-screen
                platform_x = 50 + i * (WIDTH - 150) // (base_platforms - 1)  # Better distribution
                platform_y = HEIGHT - 200 - (i * 30) - (level * 8)  # Reduced height increase
                
                # Ensure the last platform is within screen bounds
                if i == base_platforms - 1:  # Last platform
                    platform_x = min(platform_x, WIDTH - 200)  # Keep within screen
                    platform_y = max(platform_y, 100)  # Don't go too high
            
            platforms.append([platform_x, platform_y, platform_width, platform_height])
        
        # Add extra platforms for levels 11+ to fill right side space
        if level > 10:
            extra_platforms = level // 3  # Add more platforms for higher levels
            for i in range(extra_platforms):
                # Add platforms in the right side area
                extra_x = WIDTH - 300 + (i * 80)  # Start from right side
                extra_y = HEIGHT - 250 - (i * 40) - (level * 5)
                extra_width = max(30, 80 - level * 3)
                extra_height = 15
                
                # Ensure extra platforms are within screen bounds
                extra_x = max(50, min(extra_x, WIDTH - 150))
                extra_y = max(100, min(extra_y, HEIGHT - 150))
                
                platforms.append([extra_x, extra_y, extra_width, extra_height])
        
        # Generate coins
        coins = []
        for i in range(base_coins):
            if i < len(platforms):
                # Place coins on platforms
                platform = platforms[i % len(platforms)]
                coin_x = platform[0] + (platform[2] // 2) - 10
                coin_y = platform[1] - 30
            else:
                # Place coins in air
                coin_x = 100 + (i * 50) % (WIDTH - 200)
                coin_y = HEIGHT - 300 - (i * 30) % 200
            coins.append([coin_x, coin_y])
        
        # Generate obstacles with better distribution
        obstacles = []
        ground_obstacles = base_obstacles // 2
        platform_obstacles = base_obstacles - ground_obstacles
        
        # Ground obstacles - spread across full width
        for i in range(ground_obstacles):
            obstacle_width = 30 + level * 3
            obstacle_height = 40 + level * 4
            obstacle_x = 100 + (i * (WIDTH - 300) // max(1, ground_obstacles - 1))  # Better distribution
            obstacle_y = HEIGHT - obstacle_height - 10
            obstacles.append([obstacle_x, obstacle_y, obstacle_width, obstacle_height])
        
        # Platform obstacles
        for i in range(platform_obstacles):
            if i < len(platforms):
                platform = platforms[i]
                obstacle_width = 25 + level * 2
                obstacle_height = 30 + level * 3
                obstacle_x = platform[0] + (platform[2] // 2) - (obstacle_width // 2)
                obstacle_y = platform[1] - obstacle_height - 5
                obstacles.append([obstacle_x, obstacle_y, obstacle_width, obstacle_height])
        
        # Add extra obstacles for levels 11+ to fill right side space
        if level > 10:
            extra_obstacles = level // 2  # Add more obstacles for higher levels
            for i in range(extra_obstacles):
                # Add obstacles in the right side area
                extra_width = 25 + level * 2
                extra_height = 30 + level * 3
                extra_x = WIDTH - 400 + (i * 60)  # Spread across right side
                extra_y = HEIGHT - extra_height - 10
                
                # Ensure extra obstacles are within screen bounds
                extra_x = max(50, min(extra_x, WIDTH - 100))
                
                obstacles.append([extra_x, extra_y, extra_width, extra_height])
        
        # Generate enemies with better distribution
        enemies = []
        
        # Enemies increase with level - making game tougher
        num_enemies = 2 + (level // 3)  # More enemies as level increases
        for i in range(num_enemies):
            enemy_width = 30
            enemy_height = 40
            enemy_x = random.randint(50, WIDTH - 100)
            enemy_y = random.randint(120, HEIGHT - 220)
            enemy_speed = 1 + (level // 3)
            # Assign movement type based on level
            if level <= 3:
                move_type = "static"
            elif level <= 7:
                move_type = random.choice(["horizontal", "vertical"])
            elif level <= 15:
                move_type = random.choice(["horizontal", "vertical", "dynamic"])
            else:
                move_type = "dynamic"
            enemies.append([enemy_x, enemy_y, enemy_width, enemy_height, enemy_speed, 1, move_type])
        
        # Generate health pickups (fewer in higher levels) - generate first
        health_pickups = []
        for i in range(base_health_pickups):
            if i < len(platforms):
                platform = platforms[i]
                pickup_x = platform[0] + (platform[2] // 2) - 7
                pickup_y = platform[1] - 25
                health_pickups.append([pickup_x, pickup_y])
        

        
        # Generate golden bucket - ensure it's always on screen and on the last platform
        if platforms:  # If there are platforms
            last_platform = platforms[-1]  # Get the last platform
            bucket_x = last_platform[0] + (last_platform[2] // 2) - 15  # Center on platform
            bucket_y = last_platform[1] - 25  # Slightly above platform
            
            # Ensure bucket is within screen bounds
            bucket_x = max(50, min(bucket_x, WIDTH - 100))  # Keep within screen width
            bucket_y = max(50, min(bucket_y, HEIGHT - 100))  # Keep within screen height
        else:  # Fallback if no platforms
            bucket_x = WIDTH - 150
            bucket_y = HEIGHT - 100
        bucket = [bucket_x, bucket_y]
        
        # Generate guardian enemy near the bucket
        guardian_width = 40
        guardian_height = 50
        guardian_x = bucket_x - 100  # Start to the left of bucket
        guardian_y = bucket_y - 60   # Slightly above bucket
        
        # Ensure guardian is within screen bounds
        guardian_x = max(50, min(guardian_x, WIDTH - 100))
        guardian_y = max(50, min(guardian_y, HEIGHT - 100))
        
        guardian_speed = 2 + (level // 3)  # Slower speed
        guardian_enemy = [guardian_x, guardian_y, guardian_width, guardian_height, guardian_speed, 1]  # Full screen patrol
        
        return {
            'platforms': platforms,
            'coins': coins,
            'obstacles': obstacles,
            'enemies': enemies,
            'health_pickups': health_pickups,
            'background_color': background_color,
            'bucket': bucket,
            'guardian_enemy': guardian_enemy
        }

    level_props = get_level_properties(current_level)
    platforms = level_props['platforms']
    obstacles = level_props['obstacles']
    coins = level_props['coins']
    health_pickups = level_props['health_pickups']
    enemies = level_props['enemies']
    bucket = level_props['bucket']
    guardian_enemy = level_props['guardian_enemy']
    background_color = level_props['background_color']

    # Mario character drawing function
    def draw_mario(x, y, width, height):
        # Draw power-up glow effect
        if power_active:
            # Purple glow around Mario
            glow_size = 5
            pygame.draw.rect(window, LIGHT_PURPLE, (x - glow_size, y - glow_size, width + glow_size*2, height + glow_size*2))
            pygame.draw.rect(window, PURPLE, (x - glow_size, y - glow_size, width + glow_size*2, height + glow_size*2), 2)
        
        # Mario's body (red shirt)
        pygame.draw.rect(window, RED, (x, y + height//3, width, height//2))
        
        # Mario's overalls (blue)
        pygame.draw.rect(window, BLUE, (x, y + height//2, width, height//3))
        
        # Mario's head (skin color)
        pygame.draw.rect(window, (255, 200, 150), (x, y, width, height//3))
        
        # Mario's hat (red)
        pygame.draw.rect(window, RED, (x - 2, y, width + 4, height//6))
        
        # Mario's eyes (white)
        pygame.draw.circle(window, WHITE, (x + width//4, y + height//6), 3)
        pygame.draw.circle(window, WHITE, (x + 3*width//4, y + height//6), 3)
        
        # Mario's pupils (black)
        pygame.draw.circle(window, BLACK, (x + width//4, y + height//6), 1)
        pygame.draw.circle(window, BLACK, (x + 3*width//4, y + height//6), 1)
        
        # Mario's mustache (brown)
        pygame.draw.rect(window, BROWN, (x + width//4, y + height//3 - 2, width//2, 4))
        
        # Mario's arms (skin color)
        pygame.draw.rect(window, (255, 200, 150), (x - 5, y + height//3, 8, height//4))
        pygame.draw.rect(window, (255, 200, 150), (x + width - 3, y + height//3, 8, height//4))

    # Doraemon character drawing function
    def draw_doraemon(x, y, width, height):
        # Draw power-up glow effect
        if power_active:
            # Purple glow around Doraemon
            glow_size = 5
            pygame.draw.ellipse(window, LIGHT_PURPLE, (x - glow_size, y - glow_size, width + glow_size*2, height + glow_size*2))
            pygame.draw.ellipse(window, PURPLE, (x - glow_size, y - glow_size, width + glow_size*2, height + glow_size*2), 2)
        
        # Body (blue)
        pygame.draw.ellipse(window, (0, 162, 232), (x, y + height//4, width, height//2))
        # Head (white face, blue outline)
        pygame.draw.ellipse(window, (0, 162, 232), (x, y, width, height//2))
        pygame.draw.ellipse(window, (255, 255, 255), (x + 4, y + 4, width - 8, height//2 - 8))
        # Eyes
        pygame.draw.circle(window, (255, 255, 255), (x + width//3, y + height//6), 5)
        pygame.draw.circle(window, (255, 255, 255), (x + 2*width//3, y + height//6), 5)
        pygame.draw.circle(window, (0, 0, 0), (x + width//3, y + height//6), 2)
        pygame.draw.circle(window, (0, 0, 0), (x + 2*width//3, y + height//6), 2)
        # Nose (red)
        pygame.draw.circle(window, (255, 0, 0), (x + width//2, y + height//4), 3)
        # Collar (red)
        pygame.draw.rect(window, (255, 0, 0), (x, y + height//2 - 4, width, 4))

    # He-Man character drawing function
    def draw_heman(x, y, width, height):
        # Draw power-up glow effect
        if power_active:
            # Purple glow around He-Man
            glow_size = 5
            pygame.draw.rect(window, LIGHT_PURPLE, (x - glow_size, y - glow_size, width + glow_size*2, height + glow_size*2))
            pygame.draw.rect(window, PURPLE, (x - glow_size, y - glow_size, width + glow_size*2, height + glow_size*2), 2)
        
        # Body (blue armor)
        pygame.draw.rect(window, (0, 100, 200), (x, y + height//3, width, height//2))
        # Head (skin color)
        pygame.draw.ellipse(window, (255, 200, 150), (x, y, width, height//3))
        # Hair (brown)
        pygame.draw.ellipse(window, (139, 69, 19), (x - 2, y, width + 4, height//3))
        # Eyes
        pygame.draw.circle(window, (0, 0, 0), (x + width//3, y + height//6), 2)
        pygame.draw.circle(window, (0, 0, 0), (x + 2*width//3, y + height//6), 2)
        # Mustache
        pygame.draw.rect(window, (139, 69, 19), (x + width//4, y + height//3 - 2, width//2, 4))
        # Cape (red)
        pygame.draw.rect(window, (200, 0, 0), (x + width - 5, y + height//3, 8, height//2))

    # Proper red heart drawing function
    def draw_heart(x, y, size=15):
        # Heart shape using multiple circles and rectangles
        # Main heart body
        pygame.draw.circle(window, DEEP_RED, (x - size//3, y - size//3), size//3)
        pygame.draw.circle(window, DEEP_RED, (x + size//3, y - size//3), size//3)
        
        # Heart point
        points = [
            (x, y + size//2),
            (x - size//2, y - size//6),
            (x - size//3, y - size//3),
            (x, y - size//2),
            (x + size//3, y - size//3),
            (x + size//2, y - size//6)
        ]
        pygame.draw.polygon(window, DEEP_RED, points)
        
        # Bright red center
        pygame.draw.circle(window, BRIGHT_RED, (x, y), size//4)
        
        # White cross symbol
        pygame.draw.rect(window, WHITE, (x - 1, y - 4, 2, 8))
        pygame.draw.rect(window, WHITE, (x - 4, y - 1, 8, 2))
        
        # Pulsing effect
        pulse_size = int(2 * abs(pygame.time.get_ticks() % 1000 - 500) / 500)
        pygame.draw.circle(window, (255, 100, 100), (x, y), size + pulse_size, 2)

    # Golden bucket drawing function
    def draw_bucket(x, y):
        # Bucket body (gold)
        pygame.draw.rect(window, GOLD, (x - 15, y, 30, 25))
        pygame.draw.rect(window, DARK_GOLD, (x - 15, y, 30, 25), 2)
        
        # Bucket handle
        pygame.draw.arc(window, DARK_GOLD, (x - 20, y - 5, 40, 20), 0, 3.14, 3)
        
        # Gold sparkles
        sparkle_offset = (pygame.time.get_ticks() // 300) % 4
        if sparkle_offset == 0:
            pygame.draw.circle(window, WHITE, (x - 10, y - 10), 3)
        elif sparkle_offset == 1:
            pygame.draw.circle(window, WHITE, (x + 10, y - 10), 3)
        elif sparkle_offset == 2:
            pygame.draw.circle(window, WHITE, (x - 10, y + 10), 3)
        elif sparkle_offset == 3:
            pygame.draw.circle(window, WHITE, (x + 10, y + 10), 3)

    # Guardian enemy drawing function
    def draw_guardian_enemy(x, y, width, height):
        # Guardian body (darker red)
        pygame.draw.rect(window, (150, 0, 0), (x, y, width, height))
        pygame.draw.rect(window, RED, (x, y, width, height), 2)
        
        # Guardian eyes (glowing)
        pygame.draw.circle(window, (255, 255, 0), (x + 8, y + 8), 4)
        pygame.draw.circle(window, (255, 255, 0), (x + 22, y + 8), 4)
        pygame.draw.circle(window, BLACK, (x + 8, y + 8), 2)
        pygame.draw.circle(window, BLACK, (x + 22, y + 8), 2)
        
        # Guardian horns
        pygame.draw.polygon(window, (100, 0, 0), [(x + 5, y), (x + 10, y - 8), (x + 15, y)])
        pygame.draw.polygon(window, (100, 0, 0), [(x + 15, y), (x + 20, y - 8), (x + 25, y)])



    # Game loop
    running = True
    clock = pygame.time.Clock()
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  # Exit fullscreen with ESC
                    running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player_x > 0:
            player_x -= player_speed
        if keys[pygame.K_RIGHT] and player_x < WIDTH - player_width:
            player_x += player_speed
        if keys[pygame.K_SPACE] and not is_jumping and on_ground:
            is_jumping = True
            jump_count = jump_height

        # Gravity and jumping
        if is_jumping:
            if jump_count >= -jump_height:
                neg = 1
                if jump_count < 0:
                    neg = -1
                player_y -= (jump_count ** 2) * 0.5 * neg
                jump_count -= 1
            else:
                is_jumping = False

        # Apply gravity
        if not is_jumping:
            player_y += gravity

        # Platform collision detection
        on_ground = False
        player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
        
        # Check collision with platforms
        for platform in platforms:
            platform_rect = pygame.Rect(platform[0], platform[1], platform[2], platform[3])
            if player_rect.colliderect(platform_rect):
                if player_y < platform[1]:  # Landing on top of platform
                    player_y = platform[1] - player_height
                    on_ground = True
                    is_jumping = False
                elif player_y > platform[1] + platform[3]:  # Hitting platform from below
                    player_y = platform[1] + platform[3]
                elif player_x < platform[0]:  # Hitting platform from left
                    player_x = platform[0] - player_width
                else:  # Hitting platform from right
                    player_x = platform[0] + platform[2]

        # Ground collision
        if player_y >= HEIGHT - 20 - player_height:
            player_y = HEIGHT - 20 - player_height
            on_ground = True
            is_jumping = False
        
        # Upper border collision
        if player_y <= 20:
            player_y = 20
            is_jumping = False

        # Update enemies - all enemies can move anywhere on screen
        for enemy in enemies:
            move_type = enemy[6] if len(enemy) > 6 else "horizontal"
            if move_type == "static":
                pass  # No movement
            elif move_type == "horizontal":
                enemy[0] += enemy[4]  # Move horizontally
                if enemy[0] <= 0 or enemy[0] >= WIDTH - enemy[2]:
                    enemy[4] *= -1
            elif move_type == "vertical":
                enemy[1] += enemy[4]  # Move vertically
                if enemy[1] <= 20 or enemy[1] >= HEIGHT - 20 - enemy[3]:
                    enemy[4] *= -1
            elif move_type == "dynamic":
                # Zigzag: move horizontally and vertically, change vertical direction randomly
                enemy[0] += enemy[4]
                if random.randint(0, 1) == 0:
                    enemy[1] += enemy[4]
                else:
                    enemy[1] -= enemy[4]
                if enemy[0] <= 0 or enemy[0] >= WIDTH - enemy[2]:
                    enemy[4] *= -1
                if enemy[1] <= 20 or enemy[1] >= HEIGHT - 20 - enemy[3]:
                    enemy[4] *= -1

        # Update guardian enemy
        guardian_enemy[0] += guardian_enemy[4]  # Move guardian
        if guardian_enemy[0] <= 0 or guardian_enemy[0] >= WIDTH - guardian_enemy[2]:
            guardian_enemy[4] *= -1  # Reverse direction
        


        # Check collision with obstacles
        for obstacle in obstacles:
            obstacle_rect = pygame.Rect(obstacle[0], obstacle[1], obstacle[2], obstacle[3])
            if player_rect.colliderect(obstacle_rect):
                # Push player back
                if player_x < obstacle[0]:
                    player_x = obstacle[0] - player_width
                else:
                    player_x = obstacle[0] + obstacle[2]

        # Check collision with enemies and guardian
        if invincible_timer <= 0 and not power_active:  # Only check damage if not powered up
            # Regular enemies
            for enemy in enemies:
                enemy_rect = pygame.Rect(enemy[0], enemy[1], enemy[2], enemy[3])
                if player_rect.colliderect(enemy_rect):
                    player_health -= 20
                    invincible_timer = 60  # 1 second of invincibility
                    if player_health <= 0:
                        game_over_screen(window, WIDTH, HEIGHT, score, current_level)
                        return
            
            # Guardian enemy (more damage)
            guardian_rect = pygame.Rect(guardian_enemy[0], guardian_enemy[1], guardian_enemy[2], guardian_enemy[3])
            if player_rect.colliderect(guardian_rect):
                player_health -= 30  # Guardian does more damage
                invincible_timer = 60
                if player_health <= 0:
                    game_over_screen(window, WIDTH, HEIGHT, score, current_level)
                    return
            


        # Update invincibility timer
        if invincible_timer > 0:
            invincible_timer -= 1

        # Collision with health pickups
        for health_pickup in health_pickups[:]:
            pickup_rect = pygame.Rect(health_pickup[0] - 15, health_pickup[1] - 15, 30, 30)
            if player_rect.colliderect(pickup_rect):
                health_pickups.remove(health_pickup)
                player_health = min(max_health, player_health + 30)  # Restore 30 health, max 100

        # Collision with coins
        for coin in coins[:]:
            coin_rect = pygame.Rect(coin[0], coin[1], 20, 20)
            if player_rect.colliderect(coin_rect):
                coins.remove(coin)
                score += 10
                coins_collected += 1
                
                # Check if enough coins collected for power-up (but don't activate automatically)
                if coins_collected >= coins_for_power:
                    coins_collected = coins_for_power  # Cap at maximum

        # Check for power activation key press
        keys = pygame.key.get_pressed()
        if keys[pygame.K_p] and coins_collected >= coins_for_power and not power_active:
            power_active = True
            power_timer = power_duration
            coins_collected = 0  # Reset coin counter

        # Update power-up timer
        if power_active:
            power_timer -= 1
            if power_timer <= 0:
                power_active = False

        # Collision with golden bucket (level goal)
        bucket_rect = pygame.Rect(bucket[0] - 15, bucket[1], 30, 25)
        if player_rect.colliderect(bucket_rect):
            # Unlock next level
            unlock_next_level()
            if current_level <= max_levels:
                result = level_complete_screen(window, WIDTH, HEIGHT, score, current_level)
                if result == "continue":
                    # Continue to next level
                    if current_level <= max_levels:
                        run_game()  # Start next level
                        return
                elif result == "menu":
                    # Smoothly move to the level selection interface without closing/recreating root
                    pygame.display.iconify()  # Minimize the Pygame window
                    try:
                        show_level_selection()
                    except Exception:
                        start_game()
                    return
                elif result == "quit":
                    return
            else:
                game_won_screen(window, WIDTH, HEIGHT, score)
                return

        # Draw
        window.fill(background_color)
        
        # Draw upper border
        pygame.draw.rect(window, DARK_GREEN, (0, 0, WIDTH, 20))
        
        # Draw ground
        pygame.draw.rect(window, DARK_GREEN, (0, HEIGHT - 20, WIDTH, 20))
        
        # Draw platforms
        for platform in platforms:
            pygame.draw.rect(window, BROWN, (platform[0], platform[1], platform[2], platform[3]))
            # Add some texture to platforms
            pygame.draw.rect(window, (160, 82, 45), (platform[0], platform[1], platform[2], 5))
        
        # Draw obstacles (ground and platform obstacles)
        for obstacle in obstacles:
            pygame.draw.rect(window, ORANGE, (obstacle[0], obstacle[1], obstacle[2], obstacle[3]))
        
        # Draw enemies (ground and platform enemies)
        for enemy in enemies:
            pygame.draw.rect(window, RED, (enemy[0], enemy[1], enemy[2], enemy[3]))
            # Add enemy eyes
            pygame.draw.circle(window, WHITE, (enemy[0] + 8, enemy[1] + 8), 3)
            pygame.draw.circle(window, WHITE, (enemy[0] + 22, enemy[1] + 8), 3)
            pygame.draw.circle(window, BLACK, (enemy[0] + 8, enemy[1] + 8), 1)
            pygame.draw.circle(window, BLACK, (enemy[0] + 22, enemy[1] + 8), 1)
        
        # Draw guardian enemy
        draw_guardian_enemy(guardian_enemy[0], guardian_enemy[1], guardian_enemy[2], guardian_enemy[3])
        

        
        # Draw golden bucket (level goal)
        draw_bucket(bucket[0], bucket[1])
        
        # Draw health pickups (proper red hearts)
        for health_pickup in health_pickups:
            draw_heart(health_pickup[0], health_pickup[1])
        
        # Draw coins with sparkle effect (YELLOW color)
        for i, coin in enumerate(coins):
            # Main coin
            pygame.draw.circle(window, YELLOW, coin, 10)
            pygame.draw.circle(window, (255, 215, 0), coin, 8)
            # Sparkle effect
            sparkle_offset = (pygame.time.get_ticks() // 200 + i) % 4
            if sparkle_offset == 0:
                pygame.draw.circle(window, WHITE, (coin[0] - 5, coin[1] - 5), 2)
            elif sparkle_offset == 1:
                pygame.draw.circle(window, WHITE, (coin[0] + 5, coin[1] - 5), 2)
            elif sparkle_offset == 2:
                pygame.draw.circle(window, WHITE, (coin[0] - 5, coin[1] + 5), 2)
            elif sparkle_offset == 3:
                pygame.draw.circle(window, WHITE, (coin[0] + 5, coin[1] + 5), 2)
        
        # Draw Mario character (with invincibility flash)
        if invincible_timer > 0 and invincible_timer % 10 < 5:
            pass  # Don't draw player when invincible (flashing effect)
        else:
            if selected_character == "mario":
                draw_mario(player_x, player_y, player_width, player_height)
            elif selected_character == "doraemon":
                draw_doraemon(player_x, player_y, player_width, player_height)
            elif selected_character == "heman":
                draw_heman(player_x, player_y, player_width, player_height)
        
        # Draw UI
        draw_ui(window, score, player_health, current_level)
        
        pygame.display.update()
        clock.tick(60)

    pygame.quit()

def draw_ui(window, score, health, level):
    """Draw the user interface elements"""
    font = pygame.font.Font(None, 36)
    small_font = pygame.font.Font(None, 24)
    
    # Colors for UI
    GOLD = (255, 215, 0)
    PURPLE = (128, 0, 128)
    
    # Score
    score_text = font.render(f"Score: {score}", True, (255, 255, 255))
    window.blit(score_text, (10, 10))
    
    # Level display
    level_text = font.render(f"Level {level}/50", True, (255, 255, 255))
    window.blit(level_text, (20, 60))
    
    # Health bar
    health_text = small_font.render(f"Health: {health}", True, (255, 255, 255))
    window.blit(health_text, (10, 90))
    
    # Health bar visual
    bar_width = 200
    bar_height = 20
    health_percentage = health / max_health
    pygame.draw.rect(window, (255, 0, 0), (10, 120, bar_width, bar_height))
    pygame.draw.rect(window, (0, 255, 0), (10, 120, bar_width * health_percentage, bar_height))
    
    # Power-up status
    if power_active:
        power_text = small_font.render("POWER ACTIVE!", True, PURPLE)
        window.blit(power_text, (220, 90))
        
        # Power timer
        power_seconds = power_timer // 60
        timer_text = small_font.render(f"Time: {power_seconds}s", True, PURPLE)
        window.blit(timer_text, (220, 120))
    else:
        # Coin progress for power-up
        coin_text = small_font.render(f"Coins: {coins_collected}/{coins_for_power}", True, GOLD)
        window.blit(coin_text, (220, 90))
        
        if coins_collected >= coins_for_power:
            power_hint = small_font.render("Press P to activate power!", True, PURPLE)
            window.blit(power_hint, (220, 120))
        else:
            power_hint = small_font.render("Collect 5 coins for power!", True, PURPLE)
            window.blit(power_hint, (220, 120))
    
    # Health pickup indicator
    if health < max_health:
        pickup_text = small_font.render("Find red hearts to restore health!", True, (255, 50, 50))
        window.blit(pickup_text, (220, 150))
    
    # Goal indicator
    goal_text = small_font.render("Collect the golden bucket to win!", True, GOLD)
    window.blit(goal_text, (220, 180))

def game_over_screen(window, WIDTH, HEIGHT, score, level):
    """Display game over screen"""
    font = pygame.font.Font(None, 48)
    small_font = pygame.font.Font(None, 36)
    
    window.fill((0, 0, 0))
    
    game_over_text = font.render("GAME OVER", True, (255, 0, 0))
    score_text = small_font.render(f"Final Score: {score}", True, (255, 255, 255))
    level_text = small_font.render(f"Level Reached: {level}/20", True, (255, 255, 255))
    
    window.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, HEIGHT//2 - 60))
    window.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2))
    window.blit(level_text, (WIDTH//2 - level_text.get_width()//2, HEIGHT//2 + 40))
    
    pygame.display.update()
    pygame.time.wait(3000)

def level_complete_screen(window, WIDTH, HEIGHT, score, next_level):
    """Show level completion screen with continue option"""
    font = pygame.font.Font(None, 48)
    small_font = pygame.font.Font(None, 36)
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_y:
                    return "continue"
                elif event.key == pygame.K_n:
                    return "menu"
                elif event.key == pygame.K_ESCAPE:
                    return "quit"
        
        window.fill((0, 0, 0))
        
        # Congratulations text
        congrats_text = font.render(f"Congratulations!", True, (255, 215, 0))
        window.blit(congrats_text, (WIDTH//2 - congrats_text.get_width()//2, HEIGHT//2 - 100))
        
        # Level completed text
        level_text = font.render(f"Level {next_level-1} Completed!", True, (255, 255, 255))
        window.blit(level_text, (WIDTH//2 - level_text.get_width()//2, HEIGHT//2 - 50))
        
        # Score text
        score_text = small_font.render(f"Score: {score}", True, (255, 215, 0))
        window.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2))
        
        # Continue option
        if next_level <= 50:
            continue_text = small_font.render("Continue to next level? (Y/N)", True, (0, 255, 0))
            window.blit(continue_text, (WIDTH//2 - continue_text.get_width()//2, HEIGHT//2 + 50))
        else:
            win_text = small_font.render("You've completed all 50 levels!", True, (0, 255, 0))
            window.blit(win_text, (WIDTH//2 - win_text.get_width()//2, HEIGHT//2 + 50))
        
        # Instructions
        instructions = small_font.render("Press Y to continue, N for menu, ESC to quit", True, (128, 128, 128))
        window.blit(instructions, (WIDTH//2 - instructions.get_width()//2, HEIGHT//2 + 100))
        
        pygame.display.flip()
        pygame.time.wait(100)

def game_won_screen(window, WIDTH, HEIGHT, score):
    """Show game won screen"""
    font = pygame.font.Font(None, 64)
    small_font = pygame.font.Font(None, 36)
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "quit"
        
        window.fill((0, 0, 0))
        
        # Victory text
        victory_text = font.render("CONGRATULATIONS!", True, (255, 215, 0))
        window.blit(victory_text, (WIDTH//2 - victory_text.get_width()//2, HEIGHT//2 - 100))
        
        # All levels completed
        complete_text = font.render("All 50 Levels Completed!", True, (0, 255, 0))
        window.blit(complete_text, (WIDTH//2 - complete_text.get_width()//2, HEIGHT//2 - 50))
        
        # Final score
        score_text = small_font.render(f"Final Score: {score}", True, (255, 255, 255))
        window.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2))
        
        # Instructions
        instructions = small_font.render("Press ESC to quit", True, (128, 128, 128))
        window.blit(instructions, (WIDTH//2 - instructions.get_width()//2, HEIGHT//2 + 50))
        
        pygame.display.flip()
        pygame.time.wait(100)

# Tkinter GUI function
def start_game():
    show_level_selection()

def show_instructions():
    messagebox.showinfo("Instructions", 
                       "Game Controls:\n\n"
                       "• LEFT ARROW: Move left\n"
                       "• RIGHT ARROW: Move right\n"
                       "• SPACE: Jump (enhanced for long distances)\n"
                       "• P: Activate power-up (when available)\n"
                       "• ESC: Exit fullscreen\n\n"
                       "Game Features:\n"
                       "• 50 Levels with EXTREME difficulty progression\n"
                       "• Level selection with unlock system\n"
                       "• Multiple characters to choose from\n"
                       "• Enhanced jumping - reach distant platforms\n"
                       "• Platforms to jump on and collect coins\n"
                       "• Health system - avoid enemies\n"
                       "• Health pickups (red hearts) restore 30 HP\n"
                       "• Power-up system - collect 5 coins, press P to activate\n"
                       "• Invincibility power lasts 15 seconds\n"
                       "• Purple glow effect when power is active\n"
                       "• Obstacles on ground AND platforms\n"
                       "• Enemies on ground AND platforms\n"
                       "• Golden bucket goal - on the final step/platform\n"
                       "• Guardian enemy protects the golden bucket\n"
                       "• Guardian does more damage than regular enemies\n"
                       "• Fullscreen gameplay experience\n"
                       "• EXTREME difficulty scaling\n"
                       "• Fewer health pickups in higher levels\n"
                       "• Goal on last platform - final challenge\n"
                                               "• After level 10: More platforms and obstacles fill right side\n"
                        "• Enemies increase with level difficulty\n"
                        "• Upper and lower borders limit movement\n"
                        "• Golden bucket always stays within screen bounds\n\n"
                       "Objective:\n"
                       "• Use enhanced jumping to reach the final platform\n"
                       "• Collect the golden bucket on the last step\n"
                       "• Collect 5 coins then press P for invincibility power\n"
                       "• Avoid or defeat the guardian enemy\n"
                       "• Maintain your health using pickups\n"
                       "• Get the highest score possible!")

def show_character_selection():
    """Show character selection window"""
    global selected_character
    
    # Create character selection window
    char_window = tk.Toplevel(root)
    char_window.title("Character Selection")
    char_window.geometry("500x600")
    char_window.configure(bg='#2c3e50')
    char_window.resizable(False, False)
    
    # Center the window
    char_window.update_idletasks()
    x = (char_window.winfo_screenwidth() // 2) - (500 // 2)
    y = (char_window.winfo_screenheight() // 2) - (600 // 2)
    char_window.geometry(f"500x600+{x}+{y}")
    
    # Title
    title_label = tk.Label(char_window, text="Choose Your Character", 
                          font=("Arial Black", 20, "bold"), 
                          bg='#2c3e50', fg='#e74c3c')
    title_label.pack(pady=15)
    
    # Character frame with scrollbar
    canvas = tk.Canvas(char_window, bg='#2c3e50', highlightthickness=0)
    scrollbar = tk.Scrollbar(char_window, orient="vertical", command=canvas.yview)
    char_frame = tk.Frame(canvas, bg='#2c3e50')
    
    char_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=char_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True, pady=15)
    scrollbar.pack(side="right", fill="y")
    
    # Character options
    characters = [
        {
            "name": "Mario",
            "description": "Classic Nintendo hero\nRed overalls, blue shirt\nMustache and red cap\nBalanced character",
            "color": "#e74c3c",
            "value": "mario"
        },
        {
            "name": "Doraemon",
            "description": "Blue robotic cat\nWhite face, red nose\nRed collar and bell\nFriendly and helpful",
            "color": "#3498db", 
            "value": "doraemon"
        },
        {
            "name": "He-Man",
            "description": "Masters of the Universe hero\nBrown hair, muscular build\nBlue armor and red cape\nPowerful warrior",
            "color": "#ff6b35",
            "value": "heman"
        }
    ]
    
    # Create character buttons
    for char in characters:
        char_button_frame = tk.Frame(char_frame, bg='#34495e', relief="raised", bd=2)
        char_button_frame.pack(pady=8, padx=20, fill="x")
        
        # Character name
        name_label = tk.Label(char_button_frame, text=char["name"], 
                            font=("Arial Black", 16, "bold"),
                            bg='#34495e', fg=char["color"])
        name_label.pack(pady=(10, 5))
        
        # Character description
        desc_label = tk.Label(char_button_frame, text=char["description"],
                            font=("Arial", 12), bg='#34495e', fg='#ecf0f1',
                            justify="center")
        desc_label.pack(pady=(0, 10))
        
        # Select button
        select_button = tk.Button(char_button_frame, 
                                text="SELECT" if selected_character != char["value"] else "SELECTED",
                                command=lambda c=char["value"], w=char_window: select_character(c, w),
                                font=("Arial", 12, "bold"),
                                bg=char["color"], fg="white",
                                activebackground=char["color"],
                                activeforeground="white",
                                relief="raised", bd=2,
                                padx=20, pady=5)
        select_button.pack(pady=(0, 10))
        
        # Highlight current selection
        if selected_character == char["value"]:
            char_button_frame.configure(bg='#2ecc71')
            name_label.configure(bg='#2ecc71')
            desc_label.configure(bg='#2ecc71')
    
    # Current selection info
    current_label = tk.Label(char_window, 
                           text=f"Current Character: {selected_character.title()}",
                           font=("Arial", 14, "bold"),
                           bg='#2c3e50', fg='#f39c12')
    current_label.pack(side="bottom", pady=10)

def select_character(character, window):
    """Select a character and close the selection window"""
    global selected_character
    selected_character = character
    messagebox.showinfo("Character Selected", f"You have selected {character.title()}!")
    window.destroy()

# Create Tkinter window
root = tk.Tk()
root.title("Jump Quest - Enhanced Edition")
root.geometry("600x600")
root.configure(bg="#2C3E50")  # Dark blue background

# Center the window on screen
root.update_idletasks()
x = (root.winfo_screenwidth() // 2) - (600 // 2)
y = (root.winfo_screenheight() // 2) - (600 // 2)
root.geometry(f"600x600+{x}+{y}")

# Main frame
main_frame = tk.Frame(root, bg="#2C3E50", padx=40, pady=40)
main_frame.pack(expand=True, fill="both")

# Title with enhanced styling
title_label = tk.Label(main_frame, 
                      text="Jump Quest", 
                      font=("Arial Black", 32, "bold"),
                      fg="#E74C3C",  # Red color
                      bg="#2C3E50")
title_label.pack(pady=(0, 30))

# Subtitle
subtitle_label = tk.Label(main_frame,
                         text="Enhanced Edition - 50 Levels",
                         font=("Arial", 16, "italic"),
                         fg="#ECF0F1",  # Light gray
                         bg="#2C3E50")
subtitle_label.pack(pady=(0, 30))

# Button frame
button_frame = tk.Frame(main_frame, bg="#2C3E50")
button_frame.pack(pady=15)

# Start button with enhanced styling
start_button = tk.Button(button_frame, 
                        text="START GAME", 
                        command=start_game, 
                        font=("Arial Black", 18, "bold"),
                        fg="#FFFFFF",
                        bg="#27AE60",  # Green color
                        activebackground="#229954",
                        activeforeground="#FFFFFF",
                        relief="raised",
                        bd=3,
                        padx=30,
                        pady=15,
                        cursor="hand2")
start_button.pack(pady=10)

# Instructions button
instructions_button = tk.Button(button_frame,
                              text="Instructions",
                              command=show_instructions,
                              font=("Arial", 14),
                              fg="#FFFFFF",
                              bg="#3498DB",  # Blue color
                              activebackground="#2980B9",
                              activeforeground="#FFFFFF",
                              relief="raised",
                              bd=2,
                              padx=20,
                              pady=10,
                              cursor="hand2")
instructions_button.pack(pady=10)

# Character Selection button
character_button = tk.Button(button_frame,
                              text="SELECT CHARACTER",
                              command=show_character_selection,
                              font=("Arial Black", 14, "bold"),
                              fg="#FFFFFF",
                              bg="#9B59B6",  # Purple color
                              activebackground="#8E44AD",
                              activeforeground="#FFFFFF",
                              relief="raised",
                              bd=3,
                              padx=25,
                              pady=12,
                              cursor="hand2")
character_button.pack(pady=10)

# Instructions text with better formatting
instructions_frame = tk.Frame(main_frame, bg="#34495E", relief="raised", bd=2)
instructions_frame.pack(pady=20, fill="x", padx=20)

instructions_title = tk.Label(instructions_frame,
                            text="How to Play:",
                            font=("Arial", 16, "bold"),
                            fg="#F39C12",  # Orange color
                            bg="#34495E")
instructions_title.pack(pady=(15, 10))

instructions_text = tk.Label(instructions_frame,
                           text="• Use LEFT/RIGHT arrows to move\n"
                                "• Press SPACE to jump on platforms\n"
                                "• Collect yellow coins on platforms\n"
                                "• Collect red hearts to restore health\n"
                                "• Avoid red enemies and orange obstacles\n"
                                "• Enemies and obstacles on ground AND platforms\n"
                                "• Collect the golden bucket to win level\n"
                                "• Guardian enemy protects the bucket\n"
                                "• Level selection with unlock system\n"
                                "• 50 levels with EXTREME difficulty\n"
                                "• Mario-like character with detailed design\n"
                                "• Fullscreen gameplay experience\n"
                                "• EXTREME difficulty scaling\n"
                                "• Fewer health pickups in higher levels\n"
                                "• Health system - stay alive!\n"
                                "• After level 10: More platforms and obstacles\n"
                                "• Enemies increase with level difficulty\n"
                                "• Upper and lower borders limit movement\n"
                                "• Golden bucket always stays on screen",
                           font=("Arial", 12),
                           fg="#ECF0F1",
                           bg="#34495E",
                           justify="left")
instructions_text.pack(pady=(0, 15))

# Footer
footer_label = tk.Label(main_frame,
                       text="© 2024 Jump Quest - Enhanced Edition",
                       font=("Arial", 10),
                       fg="#95A5A6",  # Gray color
                       bg="#2C3E50")
footer_label.pack(side="bottom", pady=20)

# Start the GUI loop
root.mainloop()