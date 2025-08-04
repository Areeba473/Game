import pygame
import tkinter as tk
from tkinter import messagebox

# Pygame game function
def run_game():
    pygame.init()

    # Set up the display
    WIDTH = 800
    HEIGHT = 400
    window = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("PyJump Adventure")

    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GREEN = (0, 255, 0)
    YELLOW = (255, 255, 0)

    # Player properties
    player_x = 50
    player_y = HEIGHT - 70
    player_width = 40
    player_height = 40
    player_speed = 5
    jump_height = 10
    is_jumping = False
    jump_count = jump_height
    score = 0

    # Coin properties
    coins = [[random.randrange(100, WIDTH-50), random.randrange(100, HEIGHT-150)] for _ in range(5)]
    import random  # Moved here to avoid scope issues

    # Game loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player_x > 0:
            player_x -= player_speed
        if keys[pygame.K_RIGHT] and player_x < WIDTH - player_width:
            player_x += player_speed
        if keys[pygame.K_SPACE] and not is_jumping:
            is_jumping = True

        if is_jumping:
            if jump_count >= -jump_height:
                neg = 1
                if jump_count < 0:
                    neg = -1
                player_y -= (jump_count ** 2) * 0.5 * neg
                jump_count -= 1
            else:
                is_jumping = False
                jump_count = jump_height

        # Collision with coins
        player_rect = pygame.Rect(player_x, player_y, player_width, player_height)
        for coin in coins[:]:
            coin_rect = pygame.Rect(coin[0], coin[1], 20, 20)
            if player_rect.colliderect(coin_rect):
                coins.remove(coin)
                score += 1

        # Draw
        window.fill(BLACK)
        pygame.draw.rect(window, GREEN, (0, HEIGHT - 20, WIDTH, 20))  # Ground
        pygame.draw.rect(window, WHITE, (player_x, player_y, player_width, player_height))
        for coin in coins:
            pygame.draw.circle(window, YELLOW, coin, 10)
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {score}", True, WHITE)
        window.blit(score_text, (10, 10))
        pygame.display.update()

        pygame.time.Clock().tick(60)

    pygame.quit()

# Tkinter GUI function
def start_game():
    root.destroy()  # Close the GUI window
    run_game()      # Start the Pygame game

# Create Tkinter window
root = tk.Tk()
root.title("PyJump Adventure")
root.geometry("300x200")

# Add title
title_label = tk.Label(root, text="PyJump Adventure", font=("Arial", 20))
title_label.pack(pady=20)

# Add start button
start_button = tk.Button(root, text="Start Game", command=start_game, font=("Arial", 14))
start_button.pack(pady=20)

# Add instructions
instructions_label = tk.Label(root, text="Use LEFT/RIGHT to move, SPACE to jump.\nCollect coins to score!", font=("Arial", 10))
instructions_label.pack(pady=10)

# Start the GUI loop
root.mainloop()
