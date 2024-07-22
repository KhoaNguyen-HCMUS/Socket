import os
import socket
import threading


def file_chunk_generator(file_path, chunk_size):
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            yield chunk


def send_file_list(client_socket: socket.socket):
    msg = client_socket.recv(1024).decode()
    if msg == "LIST":
        with open("files_list.txt", "r") as f:
            files_list = f.read()
        client_socket.sendall(files_list.encode())


SEPARATOR = "<SEPARATOR>"


def handle_client(client_socket: socket.socket, file_list):
    try:
        file_list_str = "\n".join(
            [f"{file_name}{SEPARATOR}{file_size}" for file_name, file_size in file_list]
        )
        # client_socket.sendall(file_list_str.encode())

        manager: dict = {}

        while True:
            request = client_socket.recv(1024).decode()
            if not request:
                break

            try:
                file_name, priority = request.split(",")
            except ValueError:
                client_socket.sendall("Invalid request format".encode())
                continue

            file_path = os.path.join("Cloud", file_name)

            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)

                chunk_size = 1024
                if priority == "CRITICAL":
                    chunk_size *= 10
                elif priority == "HIGH":
                    chunk_size *= 4
                elif priority == "NORMAL":
                    chunk_size *= 1

                if not file_name in manager:
                    manager[file_name] = file_chunk_generator(file_path, chunk_size)

                client_socket.sendall(f"{file_name},{file_size}".encode())

                try:

                    chunk = next(manager[file_name])
                    client_socket.sendall(chunk)
                    # DATA{SEP}{filename}{SEP}{data}

                except StopIteration:
                    client_socket.sendall("EOF".encode())
                    continue

            else:
                client_socket.sendall("0".encode())
    finally:
        client_socket.close()


def main():
    host = "127.0.0.1"
    port = 10000
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print("Server listening on port", port)

    file_list = [
        (f, os.path.getsize(os.path.join("Cloud", f)), os.path.join("Cloud", f))
        for f in os.listdir("Cloud")
    ]

    while True:
        client_socket, addr = server_socket.accept()
        print("Connection from", addr)
        send_file_list(client_socket)
        threading.Thread(target=handle_client, args=(client_socket, file_list)).start()


if __name__ == "__main__":
    main()
