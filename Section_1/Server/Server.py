import socket
import os


class Server:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 10000

    def send_file_list(self, client_socket: socket.socket):
        message = client_socket.recv(1024).decode()
        if message == "list":
            self.handle_file_list(client_socket)

    def handle_file_list(self, client_socket: socket.socket):
        with open("files_list.txt", "r") as f:
            files_list = f.read()
        client_socket.sendall(files_list.encode())

    def send_file(self, client_socket: socket.socket, file_name):
        # Prepend the "Cloud" folder to the file_name
        server_py_directory = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(server_py_directory, "Cloud", file_name)
        # Initialize file_size
        file_size = None

        # Open files_list.txt and read file sizes
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            client_socket.sendall(str(file_size).encode())
            with open(file_path, "rb") as f:
                bytes_sent = 0
                while bytes_sent < file_size:
                    data = f.read(1024)
                    client_socket.sendall(data)
                    bytes_sent += len(data)
            print(f"Sent file: {file_name}")
        else:
            # Send a response indicating the file does not exist
            client_socket.sendall("0".encode())

    def run(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print("Server started. Waiting for connection...")
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Connection from {addr}")
            self.send_file_list(client_socket)
            try:
                while True:
                    file_name = client_socket.recv(1024).decode()
                    if not file_name:
                        break
                    self.send_file(client_socket, file_name)
            except Exception as e:
                print(f"Error: {e}")
            finally:
                client_socket.close()


if __name__ == "__main__":
    Server().run()
