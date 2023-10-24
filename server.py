import socket
import argparse
import threading
from datetime import datetime
from colorama import init, Fore, Style

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
                        userlist = ", ".join(clients.keys())
                        self.client_socket.send(f"Connected Users: {userlist}".encode('utf-8'))
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


        while True:
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            client_socket, client_address = server_socket.accept()
            print(f"[{current_time}] {client_address} Connected.")
            handler = ClientHandler(client_socket)
            handler.start()
    except OSError as e:
        if e.errno == 98:
            print("Address already in use, you wild thing :D")
        else:
            print(f"An error occurred while starting the server {e}")
    except KeyboardInterrupt:
        print("Program terminated.....")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the chat server.")
    parser.add_argument("--host", default="0.0.0.0", help="The IP address to bind the server to.")
    parser.add_argument("--port", type=int, default=12345, help="The port number to bind the server to.")
    args = parser.parse_args()

    start_server(args.host, args.port)