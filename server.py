import json
import logging
import os
import queue
import random
import socket
import threading
import time

LOG_FORMAT = '%(levelname)s | %(asctime)s | %(message)s'
LOG_LEVEL = logging.DEBUG
LOG_DIR = 'log'
LOG_FILE = os.path.join(LOG_DIR, 'client.log')

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
logging.basicConfig(filename=LOG_FILE, format=LOG_FORMAT, level=LOG_LEVEL)


clients = []
role_switch_signal = queue.Queue()
drawer_state = {'current_drawer_index': 0}
send_hi_signal = queue.Queue()
win = queue.Queue()
stop = queue.Queue()
num_of_clients = 6
stop_game = True


word_list = ["apple", "ball", "cat", "dog", "elephant", "fish", "goat", "hat",
             "ice", "jar", "kite", "lion", "moon", "net", "orange", "pen",
             "queen", "rabbit", "sun", "tiger"]
my_word1 = ''


def handle_client_connection(client_socket):
    """

    :param client_socket:
    receive messages from different clients and broadcast it to the other clients.
    also checks if the right word was written
    """
    try:
        while True:
            try:
                message = client_socket.recv(1024)
                if not message:
                    break

                message_decoded = json.loads(message.decode('utf-8'))
                logging.info('message is:', message_decoded)
                if 'chat' in message_decoded and message_decoded['chat'] == my_word1:
                    for other_client in clients:
                        try:
                            other_client.send(json.dumps({'chat': f"{my_word1} is right"}).encode('utf-8'))
                        except Exception as e:
                            logging.error(f"Error sending message to other clients: {e}")
                    role_switch_signal.put(True)
                elif 'chat' in message_decoded:
                    for other_client in clients:
                        try:
                            other_client.send(message)
                        except Exception as e:
                            logging.error(f"Error sending message to other clients: {e}")
                else:
                    for other_client in clients:
                        if other_client != client_socket:
                            try:
                                other_client.send(message)
                            except Exception as e:
                                logging.error(f"Error sending message to other clients: {e}")
            except json.JSONDecodeError as e:
                logging.error(f"JSON decode error: {e}")
            except Exception as e:
                logging.error(f"Error receiving/sending data: {e}")
                break  # Exit the loop in case of an error
    except ConnectionResetError:
        logging.warning("A client disconnected.")
    finally:
        client_socket.close()
        if client_socket in clients:
            clients.remove(client_socket)


def assign_roles():
    """
    assign the roles to the player when needed
    check when the players got 3 wins
    """
    global stop_game
    global drawer_state
    global my_word1
    my = 0
    i = True
    b = True
    num_of_right = 0
    while num_of_right != 3:
        if len(clients) == num_of_clients:
            if b:
                start_seconds = time.time()
                b = False
            drawer_state['current_drawer_index'] = 0
            clients[0].send(json.dumps({'role': 'drawer'}).encode('utf-8'))
            clients[2].send(json.dumps({'role': 'viewer'}).encode('utf-8'))
            clients[4].send(json.dumps({'role': 'viewer'}).encode('utf-8'))
            if i:
                if my == 0:
                    current_word = random.choice(word_list)
                    my_word1 = current_word
                    send_hi_signal.put(1)
                my += 1
                if my == 2:
                    my = 0
                i = False

            role_switch_signal.get()

            clients[0], clients[2] = clients[2], clients[0]

            drawer_state['current_drawer_index'] = 0
            clients[1], clients[3] = clients[3], clients[1]

            if my == 0:
                current_word = random.choice(word_list)
                my_word1 = current_word
                num_of_right += 1
                send_hi_signal.put(1)
            my += 1
            if my == 2:
                my = 0

            clients[0], clients[4] = clients[4], clients[0]

            drawer_state['current_drawer_index'] = 0
            clients[1], clients[5] = clients[5], clients[1]

            if my == 0:
                current_word = random.choice(word_list)
                my_word1 = current_word
                num_of_right += 1
                send_hi_signal.put(1)
            my += 1
            if my == 2:
                my = 0
    win.put(start_seconds)
    time.sleep(3)
    for other_client in clients:
        try:
            other_client.send(json.dumps({'quit': ''}).encode('utf-8'))
        except Exception as e:
            logging.error(f"Error sending message to other clients: {e}")
    time.sleep(1)
    stop_game = False


def start_server():
    """
    start the server for the view / draw players
    """
    global stop_game
    b = False
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('localhost', 5555))
        server_socket.listen()
        logging.info("Server listening for connections...")

        threading.Thread(target=assign_roles, daemon=True).start()

        while stop_game:
            try:
                if b:
                    server_socket.settimeout(1)  # Timeout for accept to periodically check the flag
                b = True
                client_socket, addr = server_socket.accept()
                logging.info(f"Accepted connection from {addr}")
                clients.append(client_socket)
                threading.Thread(target=handle_client_connection, args=(client_socket,), daemon=True).start()
            except Exception as e:
                logging.error(f"Error accepting connections: {e}")
    finally:
        # Modification: Explicitly close all client sockets before closing the server socket.
        for client in clients:
            try:
                client.close()
            except Exception as e:
                logging.error(f"Error closing client socket: {e}")
        server_socket.close()


def start_server2():
    """
    start the server for the chat clients
    """
    global stop_game
    b1 = False
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('localhost', 5556))
        server_socket.listen()
        logging.info("Server listening for connections...")

        while stop_game:
            try:
                if b1:
                    server_socket.settimeout(1)  # Timeout for accept to periodically check the flag
                b1 = True
                client_socket, addr = server_socket.accept()
                logging.info(f"Accepted connection from {addr}")
                clients.append(client_socket)
                threading.Thread(target=handle_client_connection, args=(client_socket,), daemon=True).start()

                threading.Thread(target=send_hi_to_drawer, daemon=True).start()
                threading.Thread(target=win1, daemon=True).start()
            except Exception as e:
                logging.error(f"Error accepting connections or starting threads: {e}")
    finally:
        # Modification: Explicitly close all client sockets before closing the server socket.
        for client in clients:
            try:
                client.close()
            except Exception as e:
                logging.error(f"Error closing client socket: {e}")
        server_socket.close()


def send_hi_to_drawer():
    """
    sends a new word to the drawing player when needed
    """
    while True:
        try:
            chat_client_index = send_hi_signal.get()
            time.sleep(0.25)
            if chat_client_index < len(clients):
                clients[3].send(json.dumps({'chat': "you are now viewer"}).encode('utf-8'))
                clients[5].send(json.dumps({'chat': "you are now viewer"}).encode('utf-8'))
                clients[chat_client_index].send(json.dumps({'chat': "you are now drawer"}).encode('utf-8'))
                clients[chat_client_index].send(json.dumps({'chat': f"your word is: {my_word1}"}).encode('utf-8'))

        except Exception as e:
            logging.error(f"Error sending 'hi' to the drawer or invalid index: {e}")


def win1():
    """
    when the players win sends them the time and closes server sockets.
    """
    while True:
        try:
            start_seconds = win.get()
            end_seconds = time.time()
            time.sleep(0.25)
            for other_client in clients:
                try:
                    other_client.send(json.dumps({'chat': "you finished the game"}).encode('utf-8'))

                except Exception as e:
                    logging.error(f"Error sending message to other clients: {e}")
            time.sleep(0.2)
            for other_client in clients:
                try:
                    other_client.send(json.dumps({'chat': f"your time was:{int(end_seconds)-int(start_seconds)}"}).encode('utf-8'))
                except Exception as e:
                    logging.error(f"Error sending message to other clients: {e}")

            time.sleep(0.2)
            for other_client in clients:
                try:
                    other_client.send(json.dumps({'chat': "game has ended"}).encode('utf-8'))
                except Exception as e:
                    logging.error(f"Error sending message to other clients: {e}")

        except Exception as e:
            logging.warning(f"Error sending 'hi' to the drawer or invalid index: {e}")


if __name__ == '__main__':
    assert isinstance(LOG_DIR, str), "LOG_DIR must be a string"
    assert isinstance(LOG_FILE, str), "LOG_FILE must be a string"
    assert isinstance(clients, list), "clients must be a list"
    assert isinstance(role_switch_signal, queue.Queue), "role_switch_signal must be a queue.Queue object"
    assert isinstance(drawer_state, dict), "drawer_state must be a dictionary"
    assert isinstance(send_hi_signal, queue.Queue), "send_hi_signal must be a queue.Queue object"
    assert isinstance(win, queue.Queue), "win must be a queue.Queue object"
    assert isinstance(stop, queue.Queue), "stop must be a queue.Queue object"
    assert isinstance(num_of_clients, int), "num_of_clients must be an integer"
    assert isinstance(stop_game, bool), "stop_game must be a boolean"
    assert isinstance(word_list, list), "word_list must be a list"
    assert isinstance(my_word1, str), "my_word1 must be a string"
    threading.Thread(target=start_server2, daemon=True).start()
    start_server()
