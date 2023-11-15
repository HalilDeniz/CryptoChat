import os
import socket
import argparse
import threading
from colorama import init, Fore, Style

init(autoreset=True)

class ChatClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client_socket = None
        self.username = None
        self.message_lock = threading.Lock()

    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
        except ConnectionRefusedError as e:
            if e.errno == 111:
                print("Connection refused")
            else:
                print(f"An unknown error occurred {e}")
            return False
        return True

    def get_username(self):
        username_prompt = self.client_socket.recv(1024).decode('utf-8')
        print(Fore.CYAN + username_prompt, end="")
        username = input()
        self.client_socket.send(username.encode('utf-8'))
        response = self.client_socket.recv(1024).decode('utf-8')
        if "Please enter a different name." in response:
            print(Fore.RED + response)
            return False
        self.username = username
        print(Fore.BLUE + "Help Menu:")
        print("\t/help       -> Help menu")
        return True

    def listen_to_server(self):
        while True:
            data = self.client_socket.recv(1024).decode('utf-8')
            if not data:
                break

            if data.strip() == "/clear":
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"{Fore.GREEN}\n\t/help       -> Help menu\n{Style.RESET_ALL}{self.username}:{Fore.YELLOW} Enter your message: {Style.RESET_ALL}",end='')
                continue

            with self.message_lock:
                if "Username changed to " in data:
                    self.username = data.split("Username changed to ")[1].rstrip(".")
                    print(f"{Fore.GREEN}\n{data}\n{Style.RESET_ALL}{self.username}:{Fore.YELLOW} Enter your message: {Style.RESET_ALL}", end='')
                else:
                    print(f"{Fore.GREEN}\n{data}\n{Style.RESET_ALL}{self.username}:{Fore.YELLOW} Enter your message: {Style.RESET_ALL}", end='')

    def send_messages(self):
        while True:
            try:
                print(f"{self.username}: {Fore.YELLOW}Enter your message: {Style.RESET_ALL}", end='')
                message = input()
                if message == "/exit":
                    self.client_socket.send(message.encode('utf-8'))
                    break
                self.client_socket.send(message.encode('utf-8'))

            except ConnectionRefusedError as e:
                if e.errno == 111:
                    print("Connection refused")
                else:
                    print(f"An unknown error occurred {e}")

            except KeyboardInterrupt:
                print(Fore.RED + "\nClosing connection...")
                self.client_socket.send("/exit".encode('utf-8'))
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
    args = parser.parse_args()

    client = ChatClient(args.host, args.port)
    client.run()
