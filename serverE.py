import socket
import base64
import hashlib
import argparse
import threading
from datetime import datetime

import cryptography.fernet
from cryptography.fernet import Fernet
from colorama import init, Fore, Style

init(autoreset=True)

clients = {}
clients_lock = threading.Lock()

class ClientHandler(threading.Thread):
    def __init__(self, client_socket):
        threading.Thread.__init__(self)
        self.client_socket = client_socket
        self.username = None

    def run(self):
        global clients

        # Ask for and validate the username
        while True:
            try:
                encrypted_prompt = cipher.encrypt("Enter your username: ".encode('utf-8'))
                self.client_socket.send(encrypted_prompt)
                encrypted_username = self.client_socket.recv(1024)
                username = cipher.decrypt(encrypted_username).decode('utf-8').strip()
                with clients_lock:
                    if username in clients or not username:
                        encrypted_error_msg = cipher.encrypt(
                            "This username is already taken or invalid. Please enter a different name.".encode('utf-8')
                        )
                        self.client_socket.send(encrypted_error_msg)
                        continue
                    else:
                        self.username = username
                        clients[self.username] = self.client_socket
                        encrypted_success_msg = cipher.encrypt("Username set successfully.".encode('utf-8'))
                        self.client_socket.send(encrypted_success_msg)
                        break
            except cryptography.fernet.InvalidToken:
                print(Fore.RED + f"Error with client: The encryption key is invalid or data is corrupted.")
                continue
            except OSError as e:
                    print(f"Error: {e}")
            except BrokenPipeError as e:
                print(f"An unknown error occurred: {e}")
            return

        # Process messages
        try:
            while True:
                encrypted_message = self.client_socket.recv(1024)
                message = cipher.decrypt(encrypted_message).decode('utf-8')

                if message == "/userlist":
                    with clients_lock:
                        userlist = ", ".join(clients.keys())
                        encrypted_response = cipher.encrypt(f"Connected Users: {userlist}".encode('utf-8'))
                        self.client_socket.send(encrypted_response)
                        continue
                if not message or message == "/exit":
                    break
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                broadcast_message = f"[{current_time}] {self.username}: {message}"
                encrypted_broadcast = cipher.encrypt(broadcast_message.encode('utf-8'))
                with clients_lock:
                    for usr, client in clients.items():
                        if usr != self.username:
                            client.send(encrypted_broadcast)
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
        print(f"{Fore.YELLOW}Default key     : {Style.RESET_ALL}{str(password)}")
        print(f"{Fore.YELLOW}Fernet Key      : {Style.RESET_ALL}{str(fernet_key)}")

        while True:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            client_socket, client_address = server_socket.accept()
            print(f"[{current_time}] {client_address} Connected.")
            handler = ClientHandler(client_socket)
            handler.start()
    except cryptography.fernet.InvalidToken:
        print(f"{Fore.RED}Incorrect Key:{Style.RESET_ALL} [{current_time}] {client_address}")
        pass
    except OSError as e:
        print(f"An error occurred while starting the server {e}")
    except KeyboardInterrupt:
        print("Program terminated.....")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the chat server.")
    parser.add_argument("--host", default="0.0.0.0", help="The IP address to bind the server to. (Default=0.0.0.0)")
    parser.add_argument("--port", type=int, default=12345, help="The port number to bind the server to. (Default=12345)")
    parser.add_argument("--key", default="mysecretpassword", help="The secret key for encryption. (Default=mysecretpassword)")
    args = parser.parse_args()

    password = args.key.encode()
    key = hashlib.sha256(password).digest()
    fernet_key = base64.urlsafe_b64encode(key)
    cipher = Fernet(fernet_key)

    start_server(args.host, args.port)
