import pygame
import sys

# Initialize pygame
pygame.init()

# Screen dimensions and creation
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))

# Title and background color
pygame.display.set_caption("Scribble")
screen.fill((255, 255, 255))  # White background

# Main loop flag
running = True
drawing = False  # Track whether the mouse button is pressed

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Check if the mouse button is pressed
        if event.type == pygame.MOUSEBUTTONDOWN:
            drawing = True
        elif event.type == pygame.MOUSEBUTTONUP:
            drawing = False

    # Draw if the mouse is pressed
    if drawing:
        mouse_position = pygame.mouse.get_pos()
        pygame.draw.circle(screen, (0, 0, 0), mouse_position, 1)  # Draw in black, with a circle radius of 1

    pygame.display.flip()

# Quit pygame
pygame.quit()
sys.exit()
