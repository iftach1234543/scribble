import pygame
import sys
import socket
import json
import threading
from multiprocessing import Process
import subprocess
import logging
import os

LOG_FORMAT = '%(levelname)s | %(asctime)s | %(message)s'
LOG_LEVEL = logging.DEBUG
LOG_DIR = 'log'
LOG_FILE = os.path.join(LOG_DIR, 'client.log')

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600


current_role = 'viewer'


if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
logging.basicConfig(filename=LOG_FILE, format=LOG_FORMAT, level=LOG_LEVEL)


def chat():
    """
    Function to launch a separate chat client process.
    """
    try:
        subprocess.run(["python", "client_3.py"])
    except Exception as e1:
        logging.error(f"Failed to launch the chat client: {e1}")


def listen_for_server_messages(client_socket, screen):
    """
    Listens and processes messages received from the server, and updates the UI accordingly.

    Parameters:
    - client_socket: The socket through which to receive messages.
    - screen: Pygame screen object for UI updates.
    - font: The font used for rendering text on the screen.
    """
    global current_role
    while True:
        try:
            msg = client_socket.recv(1)
            while not '}'.encode('utf-8') in msg:
                msg += client_socket.recv(1)
            msg = msg.decode('utf-8')
            if msg:
                data = json.loads(msg)
                if 'role' in data:
                    current_role = data['role']
                    screen.fill((255, 255, 255))
                elif 'quit' in data:
                    client_socket.close()
                    pygame.quit()
                    sys.exit()
                elif current_role == 'viewer':
                    pos_data = data.get('position')
                    if pos_data:
                        pygame.draw.circle(screen, (0, 0, 0), pos_data, 1)
        except BlockingIOError:
            pass
        except json.JSONDecodeError:
            logging.error(f"Error decoding JSON from received message:")
        except Exception as e2:
            logging.error(f"Unexpected error in message listener: {e2}")
            break


def main():
    """
    Initializes the game window, connects to the server, and handles the drawing and receiving of position data.
    """
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    pygame.display.set_caption("Scribble")
    screen.fill((255, 255, 255))

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect(('localhost', 5555))
        client_socket.setblocking(False)
    except Exception as conn_error:
        logging.error(f"Failed to connect to server: {conn_error}")
        sys.exit(1)

    global current_role

    threading.Thread(target=listen_for_server_messages, args=(client_socket, screen), daemon=True).start()

    drawing = False

    try:
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
                try:
                    pos_data = {'position': mouse_position}
                    client_socket.send(json.dumps(pos_data).encode('utf-8'))
                except Exception as send_error:
                    logging.error(f"Error sending drawing position: {send_error}")

            pygame.display.flip()
    finally:
        client_socket.close()


if __name__ == "__main__":
    logging.info("Validating environment...")
    # Ensuring the chat client script exists
    assert os.path.exists('client_3.py'), "Chat client script 'client_3.py' not found."

    p = Process(target=chat)
    p.start()
    try:
        main()
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        pygame.quit()
