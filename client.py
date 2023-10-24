import socket
import argparse
import threading
from colorama import init, Fore, Style

init(autoreset=True)

def start_client(host, port):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        message_lock = threading.Lock()
    except ConnectionRefusedError as e:
        if e.errno == 111:
            print("Connection refused")
        else:
            print(f"An unknown error occurred {e}")
        return

    # Firstly, get the username
    while True:
        username_prompt = client_socket.recv(1024).decode('utf-8')
        print(Fore.CYAN + username_prompt, end="")
        username = input()
        client_socket.send(username.encode('utf-8'))
        response = client_socket.recv(1024).decode('utf-8')
        if "Please enter a different name." not in response:
            break
        print(Fore.RED + response)
    print(Fore.BLUE + "Help Menu:")
    print("\t/exit       -> Exit the program.")
    print("\t/userlist   -> View the list of connected users.")

    # Listen for messages from the server
    def listen_to_server():
        while True:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break
            with message_lock:
                print(f"{Fore.GREEN}\n{data}\n{Style.RESET_ALL}{Fore.YELLOW}Enter your message: {Style.RESET_ALL}", end='')

    threading.Thread(target=listen_to_server, daemon=True).start()

    while True:
        try:
            print(f"{Fore.YELLOW}Enter your message: {Style.RESET_ALL}", end='')
            message = input()
            if message == "/exit":
                client_socket.send(message.encode('utf-8'))
                break
            client_socket.send(message.encode('utf-8'))
        except ConnectionRefusedError as e:
            if e.errno == 111:
                print("Connection refused")
            else:
                print(f"An unknown error occurred {e}")

        except KeyboardInterrupt:
            print(Fore.RED + "\nClosing connection...")
            client_socket.send("/exit".encode('utf-8'))
            break

    client_socket.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Connect to the chat server.")
    parser.add_argument("--host", default="127.0.0.1", help="The server's IP address.")
    parser.add_argument("--port", type=int, default=12345, help="The port number of the server.")
    args = parser.parse_args()

    start_client(args.host, args.port)