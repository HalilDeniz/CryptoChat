import os
import socket
import argparse
import threading
import base64
import hashlib
import cryptography.fernet
from cryptography.fernet import Fernet
from colorama import init, Fore, Style

init(autoreset=True)

class EncryptedChatClient:
    def __init__(self, host, port, key):
        self.host = host
        self.port = port
        self.key = key
        self.client_socket = None
        self.username = None
        self.message_lock = threading.Lock()
        self.setup_cipher()

    def setup_cipher(self):
        hashed_key = hashlib.sha256(self.key.encode()).digest()
        fernet_key = base64.urlsafe_b64encode(hashed_key)
        self.cipher = Fernet(fernet_key)

    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
        except ConnectionRefusedError as e:
            print(f"An unknown error occurred {e}")
            return False
        return True

    def get_username(self):
        try:
            encrypted_username_prompt = self.client_socket.recv(1024)
            username_prompt = self.cipher.decrypt(encrypted_username_prompt).decode('utf-8')
            print(Fore.CYAN + username_prompt, end="")
            username = input()
            encrypted_username = self.cipher.encrypt(username.encode('utf-8'))
            self.client_socket.send(encrypted_username)
            encrypted_response = self.client_socket.recv(1024)
            response = self.cipher.decrypt(encrypted_response).decode('utf-8')
            if "Please enter a different name." in response:
                print(Fore.RED + response)
                return False
            self.username = username
            print(Fore.BLUE + "Help Menu:")
            print("\t/help       -> Help menu")
            return True
        except cryptography.fernet.InvalidToken:
            print(Fore.RED + "Error: The encryption key is invalid or data is corrupted.")
            return False

    def listen_to_server(self):
        while True:
            try:
                encrypted_data = self.client_socket.recv(1024)
                decrypted_data = self.cipher.decrypt(encrypted_data).decode('utf-8')

                if decrypted_data == "/clear":
                    os.system('cls' if os.name == 'nt' else 'clear')
                    continue

                with self.message_lock:
                    if "Username changed to " in decrypted_data:
                        self.username = decrypted_data.split("Username changed to ")[1].rstrip(".")
                        print(f"{Fore.GREEN}\n{decrypted_data}\n{Style.RESET_ALL}{self.username}:{Fore.YELLOW} Enter your message: {Style.RESET_ALL}", end='')
                    else:
                        print(f"{Fore.GREEN}\n{decrypted_data}\n{Style.RESET_ALL}{self.username}:{Fore.YELLOW} Enter your message: {Style.RESET_ALL}", end='')
            except cryptography.fernet.InvalidToken:
                continue
            except BrokenPipeError as e:
                if e.errno == 32:
                    continue
                else:
                    print(e)

    def send_messages(self):
        while True:
            try:
                print(f"{self.username}:{Fore.YELLOW} Enter your message: {Style.RESET_ALL}", end='')
                message = input()
                if not message:
                    continue
                encrypted_message = self.cipher.encrypt(message.encode('utf-8'))
                self.client_socket.send(encrypted_message)
                if message == "/exit":
                    break
            except cryptography.fernet.InvalidToken:
                continue
            except ConnectionRefusedError as e:
                print(f"An unknown error occurred {e}")
                break
            except KeyboardInterrupt:
                print(Fore.RED + "\nClosing connection...")
                self.client_socket.send(self.cipher.encrypt("/exit".encode('utf-8')))
                break

    def run(self):
        if self.connect():
            if self.get_username():
                threading.Thread(target=self.listen_to_server, daemon=True).start()
                self.send_messages()
        self.client_socket.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Connect to the chat server.")
    parser.add_argument("--host", default="127.0.0.1", help="The server's IP address.")
    parser.add_argument("--port", type=int, default=12345, help="The port number of the server.")
    parser.add_argument("--key", default="mysecretpassword", help="The secret key for encryption.")
    args = parser.parse_args()

    client = EncryptedChatClient(args.host, args.port, args.key)
    client.run()
