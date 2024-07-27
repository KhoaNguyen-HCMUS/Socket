import os
import socket
import threading

SEPARATOR = " "
FORMAT = "utf-8"


class Server:
    def __init__(self, host="127.0.0.1", port=65432):
        self.host = host
        self.port = port
        self.server_socket = None
        self.socket_list = {}

    def gen_file_list(self, file_path):
        with open(file_path, "w") as f:
            for file_name in os.listdir("Cloud"):
                f.write(
                    f'{file_name}{SEPARATOR}{str(os.path.getsize(os.path.join("Cloud", file_name)))}\n'
                )

    def send_file_list(self, client_socket: socket.socket):
        msg = client_socket.recv(1024).decode(FORMAT)
        if msg == "LIST":
            with open("file_list.txt", "r") as f:
                file_list = f.read()
            client_socket.sendall(file_list.encode(FORMAT))
        else:
            print("\nInvalid command.")

    def file_chunk_generator(self, file_path, chunk_size):
        with open(file_path, "rb") as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    yield b"EOF"
                    break
                yield data

    def handle_client(self, client_socket: socket.socket, addr):
        self.send_file_list(client_socket)
        download_manager = {}
        try:
            while True:
                cmd = client_socket.recv(1024).decode(FORMAT)
                if cmd == "get":
                    while True:
                        request = client_socket.recv(1024).decode(FORMAT)
                        if request[:4] == "done":
                            break
                        if request[:9] == "terminate":
                            client_socket.close()
                            print("Client", addr, "disconnected.")
                            return

                        _, file_name, priority_size = request.split(SEPARATOR)
                        self.send_data(client_socket, file_name, int(priority_size), download_manager)
                elif cmd == "terminate":
                    client_socket.close()
                    print("Client", addr, "disconnected.")
                    break
        except Exception as e:
            print(
                f"Error: Client {self.socket_list[client_socket]} was forcibly closed by the remote host."
            )
            client_socket.close()

    def send_data(self, client_socket: socket.socket, file_name, priority_size, download_manager):
        file_path = os.path.join("Cloud", file_name)
        chunk_size = priority_size

        if file_name not in download_manager:
            download_manager[file_name] = self.file_chunk_generator(
                file_path, chunk_size
            )
        try:
            data = next(download_manager[file_name])
            client_socket.sendall(data)
        except StopIteration:
            del download_manager[file_name]

    def process(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            self.socket_list[client_socket] = addr
            print("Client", addr, "connected.")
            client_thread = threading.Thread(
                target=self.handle_client, args=(client_socket, addr)
            )
            client_thread.start()

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

        print("Server listening on port", self.port)

        self.gen_file_list("file_list.txt")

        process_thread = threading.Thread(target=self.process)
        process_thread.start()


if __name__ == "__main__":
    server = Server()
    server.start()
