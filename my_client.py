import pygame
import sys
import socket
import json
import threading

pygame.init()

blue = (0,0,128)
green = (0, 255, 0)

screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))

pygame.display.set_caption("Scribble")
screen.fill((255, 255, 255))  # White background

font = pygame.font.Font('freesansbold.ttf', 32)
text = font.render('hi', True, green, blue)

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 5555))
client_socket.setblocking(False)

current_role = 'viewer'

def listen_for_server_messages():
    global current_role
    while True:
        try:
            msg = client_socket.recv(1024).decode('utf-8')
            if msg:
                data = json.loads(msg)
                if 'role' in data:
                    current_role = data['role']
                    screen.fill((255, 255, 255))  # Clear screen on role switch
                elif current_role == 'viewer':
                    pos_data = data.get('position')
                    if pos_data:
                        pygame.draw.circle(screen, (0, 0, 0), pos_data, 1)
        except BlockingIOError:
            pass

threading.Thread(target=listen_for_server_messages, daemon=True).start()

drawing = False

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            drawing = True
        elif event.type == pygame.MOUSEBUTTONUP:
            drawing = False

    if current_role == 'drawer' and drawing:
        mouse_position = pygame.mouse.get_pos()
        pygame.draw.circle(screen, (0, 0, 0), mouse_position, 1)
        pos_data = {'position': mouse_position}
        client_socket.send(json.dumps(pos_data).encode('utf-8'))

    pygame.display.flip()

server:import socket
import threading
import time
import json

clients = []

def handle_client_connection(client_socket):
    try:
        while True:
            message = client_socket.recv(1024)
            for other_client in clients:
                if other_client != client_socket:
                    other_client.send(message)
    except ConnectionResetError:
        print("A client disconnected.")
    finally:
        client_socket.close()
        clients.remove(client_socket)

def assign_roles():
    while True:
        if len(clients) == 2:
            # Initially assign roles
            clients[0].send(json.dumps({'role': 'drawer'}).encode('utf-8'))
            clients[1].send(json.dumps({'role': 'viewer'}).encode('utf-8'))
            time.sleep(30)  # Switch roles every 30 seconds

            # Switch roles
            clients[0], clients[1] = clients[1], clients[0]  # Swap clients

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('localhost', 5555))
    server_socket.listen()
    print("Server listening for connections...")

    threading.Thread(target=assign_roles, daemon=True).start()

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Accepted connection from {addr}")
        clients.append(client_socket)
        threading.Thread(target=handle_client_connection, args=(client_socket,), daemon=True).start()

if __name__ == '__main__':
    start_server()
