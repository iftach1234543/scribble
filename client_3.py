import pygame
import sys
import socket
import json
import threading
import time
import logging
import os

messages = []
current_role = 'viewer'

LOG_FORMAT = '%(levelname)s | %(asctime)s | %(message)s'
LOG_LEVEL = logging.DEBUG
LOG_DIR = 'log'
LOG_FILE = os.path.join(LOG_DIR, 'lucky.log')

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
logging.basicConfig(filename=LOG_FILE, level=LOG_LEVEL, format=LOG_FORMAT)


def listen_for_server_messages(client_socket, screen, blue, green, chat_font):
    """
    Listens for incoming messages from the server. Upon receiving a message, it decodes it
    and adds it to the buffer. It then tries to parse and handle complete messages from the buffer.

    Parameters:
    - client_socket: The socket connection to the server.
    - screen: The Pygame surface to draw the messages on.
    - blue, green: The colors used for rendering text background.
    - chat_font: The Pygame font used for rendering chat messages.
    """
    buffer = ""
    while True:
        try:
            msg = client_socket.recv(1)
            while not '}'.encode('utf-8') in msg:
                msg += client_socket.recv(1)
            msg = msg.decode('utf-8')
            if msg:
                buffer += msg
                while buffer:
                    try:
                        data, index = json.JSONDecoder().raw_decode(buffer)
                        buffer = buffer[index:].lstrip()
                        handle_message(data, screen, blue, green, chat_font)
                    except json.JSONDecodeError:
                        break
        except BlockingIOError:
            pass
        except Exception as ex:
            logging.error(f"Error in listen_for_server_messages: {ex}")
            break


def handle_message(data, screen, blue, green, chat_font):
    """
    Handles messages received from the server by taking appropriate actions based on the message type.

    Parameters:
    - data: Decoded JSON data from the server.
    - screen: Pygame surface for drawing.
    - blue, green: Colors for message background and text.
    - chat_font: Pygame font object for rendering chat messages.
    """
    global current_role, messages
    screen.fill((255, 255, 255))  # Clear screen with white background

    if 'role' in data:
        current_role = data['role']
    elif 'quit' in data:
        pygame.quit()
        sys.exit()
    elif 'position' in data and current_role == 'viewer':
        pos_data = data.get('position')
        pygame.draw.circle(screen, (0, 0, 0), pos_data, 1)
    elif 'chat' in data or 'system_message' in data:
        chat_message = data.get('chat', '')
        lines = [chat_message[i:i + 30] for i in range(0, len(chat_message), 30)]
        messages = lines + messages
        messages = messages[:5]  # Keep only the 5 most recent messages

    y_offset = 10
    for message in messages:
        text = chat_font.render(message, True, green, blue)
        screen.blit(text, (10, y_offset))
        y_offset += 25


def send_message(message, client_socket):
    """
    Encodes and sends a chat message to the server.

    Parameters:
    - message: The chat message to send.
    - client_socket: The socket connection to the server.
    """
    try:
        client_socket.send(json.dumps({'chat': message}).encode('utf-8'))
    except Exception as e:
        logging.error(f"Error sending message: {e}")


def main():
    """
    Initializes game window, establishes server connection, and controls main game loop.
    """
    pygame.init()
    blue = (0, 0, 128)
    green = (0, 255, 0)

    time.sleep(0.5)
    screen_width, screen_height = 400, 300
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Scribble")
    screen.fill((255, 255, 255))  # White background

    font = pygame.font.Font('freesansbold.ttf', 20)
    chat_font = pygame.font.Font('freesansbold.ttf', 18)

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect(('localhost', 5556))
        client_socket.setblocking(False)
    except ConnectionRefusedError:
        logging.error("Unable to connect to the server.")
        sys.exit()

    threading.Thread(target=listen_for_server_messages, args=(client_socket, screen, blue, green, chat_font), daemon=True).start()

    chat_input = ""
    chat_surface = pygame.Surface((screen_width - 20, 30))
    chat_rect = chat_surface.get_rect(center=(screen_width / 2, screen_height - 40))
    send_button = pygame.Rect(screen_width - 80, screen_height - 40, 70, 30)

    while True:
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if send_button.collidepoint(event.pos) and chat_input:
                        send_message(chat_input, client_socket)
                        chat_input = ""
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and chat_input:
                        send_message(chat_input, client_socket)
                        chat_input = ""
                    elif event.key == pygame.K_BACKSPACE:
                        chat_input = chat_input[:-1]
                    else:
                        chat_input += event.unicode
        except pygame.error:
            logging.error('video sys not initialised')
            break

        # Refreshing the display with current messages and chat input
        screen.fill((255, 255, 255))
        handle_message({}, screen, blue, green, chat_font)  # Re-render messages on every loop

        pygame.draw.rect(screen, (200, 200, 200), chat_rect, 2)
        chat_surface.fill((255, 255, 255))
        chat_text = font.render(chat_input, True, (0, 0, 0))
        chat_surface.blit(chat_text, (5, 5))
        screen.blit(chat_surface, chat_rect.topleft)

        pygame.draw.rect(screen, (0, 255, 0), send_button)
        send_text = font.render("Send", True, (255, 255, 255))
        screen.blit(send_text, send_button.topleft)

        pygame.display.flip()


if __name__ == "__main__":
    logging.info("Validating environment...")
    assert socket.gethostbyname('localhost'), "Unable to resolve 'localhost'. Check your network configuration."
    logging.info("Environment validated. Starting the client...")
    logging.info("Starting the client...")
    main()
