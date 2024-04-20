import pygame
import sys
import socket
import json
import threading

# Initialize Pygame
pygame.init()
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Drawing Game")
screen.fill((255, 255, 255))  # White background

# Set up socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 5555))
client_socket.setblocking(False)

current_role = 'viewer'  # Default role

def listen_for_role():
    global current_role
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            data = json.loads(message)
            if 'role' in data:
                current_role = data['role']
                print(f"Now you are the {current_role}.")
        except BlockingIOError:
            pass
        except json.JSONDecodeError:
            pass

threading.Thread(target=listen_for_role, daemon=True).start()

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    if current_role == 'drawer':
        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0]:  # If the left mouse button is pressed
            position = pygame.mouse.get_pos()
            pygame.draw.circle(screen, (0, 0, 0), position, 1)
            # Send drawing position to the server
            try:
                message = json.dumps({'action': 'draw', 'position': position})
                client_socket.send(message.encode('utf-8'))
            except BlockingIOError:
                pass
            except BrokenPipeError:
                print("Server disconnected.")
                running = False
                break
    pygame.display.flip()

client_socket.close()
pygame.quit()
sys.exit()
