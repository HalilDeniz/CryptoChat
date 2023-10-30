import os
import socket
import logging
import argparse
import threading
from datetime import datetime
from colorama import init, Fore, Style

clients = {}
clients_lock = threading.Lock()

def log_setup(loglevel, logfile):
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {loglevel}")

    logging.basicConfig(level=numeric_level,
                        format="%(asctime)s [%(levelname)s] - %(message)s",
                        handlers=[logging.FileHandler(logfile),
                                  logging.StreamHandler()])

class ClientHandler(threading.Thread):
    def __init__(self, client_socket):
        threading.Thread.__init__(self)
        self.client_socket = client_socket
        self.username = None

    def run(self):
        global clients
        logging.info(f"New client connected: {self.client_socket.getpeername()}")  # Eklenen log


        # Ask for and validate the username
        while True:
            try:
                self.client_socket.send("Enter your username: ".encode('utf-8'))
                username = self.client_socket.recv(1024).decode('utf-8').strip()
                with clients_lock:
                    if username in clients or not username:
                        self.client_socket.send(
                            "This username is already taken or invalid. Please enter a different name.".encode('utf-8'))
                        continue  # After sending the error message, return to the beginning of the loop
                    else:
                        self.username = username
                        clients[self.username] = self.client_socket
                        self.client_socket.send("Username set successfully.".encode('utf-8'))
                        break

            except BrokenPipeError as e:
                if e.errno == 32:
                    pass
                else:
                    print(f"An unknown error occurred: {e}")
                return
        # Process messages
        try:
            while True:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message == "/userlist":
                    with clients_lock:
                        userlist = "\n".join([f"\t{i + 1}) {user}" for i, user in enumerate(clients.keys())])
                        response = f"Connected Users:\n{userlist}"
                        self.client_socket.send(response.encode('utf-8'))
                        continue
                if message == "/help":
                    response = Fore.BLUE + "Help Menu:\n" \
                                        "\t/help                           -> Help Menu\n" \
                                        "\t/exit                           -> Exit the program.\n" \
                                        "\t/userlist                       -> View the list of connected users.\n" \
                                        "\t/dm [user] [message]            -> Send a direct message to a user.\n" \
                                        "\t/changeuser [new_username]      -> Change your username.\n"
                    self.client_socket.send(response.encode('utf-8'))
                    continue
                if message.startswith("/changeuser "):
                    _, new_username = message.split()
                    with clients_lock:
                        if new_username in clients:
                            self.client_socket.send(
                                "This username is already taken. Please choose another one.".encode('utf-8'))
                        else:
                            # Remove the old username and add the new one
                            del clients[self.username]
                            self.username = new_username
                            clients[self.username] = self.client_socket
                            self.client_socket.send(f"Username changed to {new_username}.".encode('utf-8'))
                    continue

                if message.startswith("/dm "):
                    _, recipient, *dm_msg_parts = message.split()
                    dm_message = " ".join(dm_msg_parts)
                    with clients_lock:
                        if recipient in clients:
                            clients[recipient].send(f"[DM from {self.username}] {dm_message}".encode('utf-8'))
                            self.client_socket.send(f"[DM to {recipient}] {dm_message}".encode('utf-8'))
                        else:
                            self.client_socket.send("Specified user not found.".encode('utf-8'))
                    continue
                if not message or message == "/exit":
                    break
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                broadcast_message = f"[{current_time}] {self.username}: {message}"
                with clients_lock:
                    for usr, client in clients.items():
                        if usr != self.username:
                            client.send(broadcast_message.encode('utf-8'))
        except:
            pass

        # Cleanup when the client exits
        with clients_lock:
            del clients[self.username]
        self.client_socket.close()

def start_server(host, port):
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        host_ip, host_port = server_socket.getsockname()
        server_socket.listen(5)
        print("Server started. Waiting for clients...")
        print(f"{Fore.YELLOW}Host information: {Style.RESET_ALL}{host_ip}:{host_port}")
        logging.info(f"Server started on {host_ip}:{host_port}")  # Eklenen log

        while True:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            client_socket, client_address = server_socket.accept()
            print(f"[{current_time}] {client_address} Connected.")
            logging.info(f"Accepted connection from {client_address}")  # Eklenen log
            handler = ClientHandler(client_socket)
            handler.start()

    except OSError as e:
        if e.errno == 98:
            print("Address already in use, you wild thing :D")
            logging.error("Address already in use")  # Eklenen log
        else:
            print(f"An error occurred while starting the server: {e}")
            logging.error(f"An error occurred: {e}")  # Eklenen log
    except KeyboardInterrupt:
        print("Program terminated.....")
        logging.info("Server was terminated by keyboard interrupt")  # Eklenen log


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the chat server.")
    parser.add_argument("--host", default="0.0.0.0", help="The IP address to bind the server to. (Default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=12345, help="The port number to bind the server to. (Default: 12345)")
    parser.add_argument("--loglevel", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],help="Set the logging level (Default: INFO)")
    parser.add_argument("--logfile", default="server.log", help="Set the log file name. (Default: server.log")
    args = parser.parse_args()

    log_setup(args.loglevel, args.logfile)  # Log ayarlarını başlatma

    start_server(args.host, args.port)
