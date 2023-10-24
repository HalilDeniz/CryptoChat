import argparse
import base64
import hashlib
import socket
import threading

import cryptography.fernet
from colorama import init, Fore, Style
from cryptography.fernet import Fernet

init(autoreset=True)


def start_client(host, port):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        message_lock = threading.Lock()
    except ConnectionRefusedError as e:
        print(f"An unknown error occurred {e}")
        return

    # Firstly, get the username
    while True:
        try:
            encrypted_username_prompt = client_socket.recv(1024)
            username_prompt = cipher.decrypt(encrypted_username_prompt).decode('utf-8')
            print(Fore.CYAN + username_prompt, end="")
            username = input()
            encrypted_username = cipher.encrypt(username.encode('utf-8'))
            client_socket.send(encrypted_username)
            encrypted_response = client_socket.recv(1024)
            response = cipher.decrypt(encrypted_response).decode('utf-8')
            if "Please enter a different name." not in response:
                break
            print(Fore.RED + response)
        except cryptography.fernet.InvalidToken:
            print(Fore.RED + "Error: The encryption key is invalid or data is corrupted.")
            quit(0)
        except KeyboardInterrupt:
            quit(0)
    print(Fore.BLUE + "Help Menu:")
    print("\t/exit       -> Exit the program.")
    print("\t/userlist   -> View the list of connected users.")

    # Listen for messages from the server
    def listen_to_server():
        while True:
            encrypted_data = client_socket.recv(1024)
            decrypted_data = cipher.decrypt(encrypted_data).decode('utf-8')
            if not decrypted_data:
                break
            with message_lock:
                print(f"{Fore.GREEN}\n{decrypted_data}\n{Style.RESET_ALL}{Fore.YELLOW}Enter your message: {Style.RESET_ALL}", end='')

    threading.Thread(target=listen_to_server, daemon=True).start()

    while True:
        try:
            print(f"{Fore.YELLOW}Enter your message: {Style.RESET_ALL}", end='')
            message = input()
            encrypted_message = cipher.encrypt(message.encode('utf-8'))
            client_socket.send(encrypted_message)
            if message == "/exit":
                break
        except ConnectionRefusedError as e:
            print(f"An unknown error occurred {e}")
            break
        except KeyboardInterrupt:
            print(Fore.RED + "\nClosing connection...")
            client_socket.send(cipher.encrypt("/exit".encode('utf-8')))
            break

    client_socket.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Connect to the chat server.")
    parser.add_argument("--host", default="127.0.0.1", help="The IP address to bind the server to. (Default=127.0.0.1)")
    parser.add_argument("--port", type=int, default=12345, help="The port number to bind the server to. (Default=12345)")
    parser.add_argument("--key", default="mysecretpassword", help="The secret key for encryption. (Default=mysecretpassword)")
    args = parser.parse_args()

    password = args.key.encode()
    key = hashlib.sha256(password).digest()
    fernet_key = base64.urlsafe_b64encode(key)
    cipher = Fernet(fernet_key)

    start_client(args.host, args.port)
