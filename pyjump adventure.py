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
    pygame.display.set_caption(f"PyJump Adventure - Level {current_level}")

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
    player_width = 30
    player_height = 40
    player_x = 50
    player_y = HEIGHT - player_height - 10
    player_speed = 6  # Balanced speed
    jump_height = HEIGHT // 50  # Set to exactly 2% of screen height
    is_jumping = False
    jump_count = jump_height
    score = 0
    invincible_timer = 0
    on_ground = False
    gravity = 0.5  # Reduced gravity for longer air time to reach platforms

    # Reset power-up variables for new level
    power_active = False
    power_timer = 0
    coins_collected = 0

    # Level-specific properties with platforms
    def get_level_properties(level):
        """Generate level properties based on level number"""
        
        # Scale difficulty with level
        base_platforms = 3 + (level // 2) + (level // 5)
        base_coins = 5 + level * 3
        base_obstacles = 2 + level + (level // 3)
        base_enemies = level // 2 + (level // 4)
        base_health_pickups = 2 + (level // 4)
        
        # Background color gets darker with level
        if level <= 3:
            background_color = LIGHT_BLUE
        elif level <= 8:
            background_color = (20, 20, 40)
        elif level <= 12:
            background_color = (40, 20, 20)
        elif level <= 16:
            background_color = (20, 20, 20)
        elif level <= 25:
            background_color = (10, 10, 10)
        elif level <= 35:
            background_color = (5, 5, 5)
        elif level <= 45:
            background_color = (2, 2, 2)
        else:
            background_color = (0, 0, 0)
        
        # Generate platforms
        platforms = []
        for i in range(base_platforms):
            platform_width = max(40, 120 - level * 6)
            platform_height = 20
            platform_x = 50 + i * (WIDTH - 100) // base_platforms
            platform_y = HEIGHT - 200 - (i * 50) - (level * 15)
            platforms.append([platform_x, platform_y, platform_width, platform_height])
        
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
        
        # Generate obstacles
        obstacles = []
        ground_obstacles = base_obstacles // 2
        platform_obstacles = base_obstacles - ground_obstacles
        
        # Ground obstacles
        for i in range(ground_obstacles):
            obstacle_width = 30 + level * 3
            obstacle_height = 40 + level * 4
            obstacle_x = 100 + (i * 200) % (WIDTH - 200)
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
        
        # Generate enemies
        enemies = []
        ground_enemies = base_enemies // 2
        platform_enemies = base_enemies - ground_enemies
        
        # Ground enemies
        for i in range(ground_enemies):
            enemy_width = 30
            enemy_height = 40
            enemy_x = 150 + (i * 300) % (WIDTH - 200)
            enemy_y = HEIGHT - enemy_height - 10
            enemy_speed = 2 + level + (level // 2)
            enemies.append([enemy_x, enemy_y, enemy_width, enemy_height, enemy_speed, 1])  # 1 = direction
        
        # Platform enemies
        for i in range(platform_enemies):
            if i < len(platforms):
                platform = platforms[i]
                enemy_width = 25
                enemy_height = 35
                enemy_x = platform[0] + 10
                enemy_y = platform[1] - enemy_height - 5
                enemy_speed = 1 + level + (level // 3)
                enemies.append([enemy_x, enemy_y, enemy_width, enemy_height, enemy_speed, 1, platform[0], platform[0] + platform[2]])  # Platform bounds
        
        # Generate health pickups (fewer in higher levels)
        health_pickups = []
        for i in range(base_health_pickups):
            if i < len(platforms):
                platform = platforms[i]
                pickup_x = platform[0] + (platform[2] // 2) - 7
                pickup_y = platform[1] - 25
                health_pickups.append([pickup_x, pickup_y])
        
        # Generate golden bucket - always on the last platform (final step)
        if platforms:  # If there are platforms
            last_platform = platforms[-1]  # Get the last platform
            bucket_x = last_platform[0] + (last_platform[2] // 2) - 15  # Center on platform
            bucket_y = last_platform[1] - 25  # Slightly above platform
        else:  # Fallback if no platforms
            bucket_x = WIDTH - 150
            bucket_y = HEIGHT - 100
        bucket = [bucket_x, bucket_y]
        
        # Generate guardian enemy near the bucket
        guardian_width = 40
        guardian_height = 50
        guardian_x = bucket_x - 100  # Start to the left of bucket
        guardian_y = bucket_y - 60   # Slightly above bucket
        guardian_speed = 3 + level + (level // 2)
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

        # Update enemies with platform patrolling
        for enemy in enemies:
            if len(enemy) == 8:  # Platform enemy with patrol bounds
                enemy[0] += enemy[4]  # Move enemy
                if enemy[0] <= enemy[6] or enemy[0] >= enemy[7]:  # Check platform bounds
                    enemy[4] *= -1  # Reverse direction
            else:  # Ground enemy (6 elements)
                enemy[0] += enemy[4]  # Move enemy
                if enemy[0] <= 0 or enemy[0] >= WIDTH - enemy[2]:
                    enemy[4] *= -1  # Reverse direction

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
                    # Return to level selection
                    return
                elif result == "quit":
                    return
            else:
                game_won_screen(window, WIDTH, HEIGHT, score)
                return

        # Draw
        window.fill(background_color)
        
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
            draw_mario(player_x, player_y, player_width, player_height)
        
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
                       "• Mario-like character with detailed design\n"
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
                       "• Goal on last platform - final challenge\n\n"
                       "Objective:\n"
                       "• Use enhanced jumping to reach the final platform\n"
                       "• Collect the golden bucket on the last step\n"
                       "• Collect 5 coins then press P for invincibility power\n"
                       "• Avoid or defeat the guardian enemy\n"
                       "• Maintain your health using pickups\n"
                       "• Get the highest score possible!")

# Create Tkinter window
root = tk.Tk()
root.title("PyJump Adventure - Enhanced Edition")
root.geometry("600x500")
root.configure(bg="#2C3E50")  # Dark blue background

# Center the window on screen
root.update_idletasks()
x = (root.winfo_screenwidth() // 2) - (600 // 2)
y = (root.winfo_screenheight() // 2) - (500 // 2)
root.geometry(f"600x500+{x}+{y}")

# Main frame
main_frame = tk.Frame(root, bg="#2C3E50", padx=40, pady=40)
main_frame.pack(expand=True, fill="both")

# Title with enhanced styling
title_label = tk.Label(main_frame, 
                      text="PyJump Adventure", 
                      font=("Arial Black", 32, "bold"),
                      fg="#E74C3C",  # Red color
                      bg="#2C3E50")
title_label.pack(pady=(0, 30))

# Subtitle
subtitle_label = tk.Label(main_frame,
                         text="Enhanced Edition - 20 Levels",
                         font=("Arial", 16, "italic"),
                         fg="#ECF0F1",  # Light gray
                         bg="#2C3E50")
subtitle_label.pack(pady=(0, 40))

# Button frame
button_frame = tk.Frame(main_frame, bg="#2C3E50")
button_frame.pack(pady=20)

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

# Instructions text with better formatting
instructions_frame = tk.Frame(main_frame, bg="#34495E", relief="raised", bd=2)
instructions_frame.pack(pady=30, fill="x", padx=20)

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
                                "• 20 levels with EXTREME difficulty\n"
                                "• Mario-like character with detailed design\n"
                                "• Fullscreen gameplay experience\n"
                                "• EXTREME difficulty scaling\n"
                                "• Fewer health pickups in higher levels\n"
                                "• Health system - stay alive!",
                           font=("Arial", 12),
                           fg="#ECF0F1",
                           bg="#34495E",
                           justify="left")
instructions_text.pack(pady=(0, 15))

# Footer
footer_label = tk.Label(main_frame,
                       text="© 2024 PyJump Adventure - Enhanced Edition",
                       font=("Arial", 10),
                       fg="#95A5A6",  # Gray color
                       bg="#2C3E50")
footer_label.pack(side="bottom", pady=20)

# Start the GUI loop
root.mainloop()