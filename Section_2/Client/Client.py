import os
import socket
import sys
import time


def read_input_file():
    with open("input.txt", "r") as file:
        return [tuple(line.strip().split(",")) for line in file.readlines()]


def write_file(file_path, data):
    with open(file_path, "ab") as f:
        f.write(data)


def manage_file(file_path, file_size, client_socket):
    downloaded_size = 0
    os.makedirs("output", exist_ok=True)
    with open(os.path.join("output", file_path), "wb") as f:
        while downloaded_size < file_size:
            data = client_socket.recv(1024)
            f.write(data)
            downloaded_size += len(data)
            percent = 100.0 * downloaded_size / file_size
            bar_length = 30
            sys.stdout.write(
                f"\r{file_path:<20} [{'=' * int(bar_length * percent / 100):<30}] {percent:.2f}%"
            )
            sys.stdout.flush()
    print("\nDownload complete")


def request_file_download(client_socket: socket.socket, file_name, priority):
    client_socket.sendall(f"{file_name},{priority}".encode())
    response = client_socket.recv(1024).decode()

    try:
        file_name, file_size = response.split(",")
        file_size = int(file_size)
    except ValueError:
        print("Invalid response format from server")
        return


    if file_size > 0:
        downloaded_size = 0
        os.makedirs("output", exist_ok=True)
        with open(os.path.join("output", file_name), "wb") as f:
            while downloaded_size < file_size:
                data = client_socket.recv(1024)
                f.write(data)
                downloaded_size += len(data)
                percent = 100.0 * downloaded_size / file_size
                bar_length = 30
                sys.stdout.write(
                    f"\r{file_name:<20} [{'=' * int(bar_length * percent / 100):<30}] {percent:.2f}%"
                )
                sys.stdout.flush()
        print("\nDownload complete")
    else:
        print("File not found or empty")


def monitor_input_file(client_socket: socket.socket):
    downloaded_files = set()
    last_modified = 0

    while True:
        current_modified = os.path.getmtime("input.txt")
        if current_modified > last_modified:
            last_modified = current_modified
            input_files = read_input_file()
            for file_name, priority in input_files:
                if (file_name, priority) not in downloaded_files:
                    request_file_download(client_socket, file_name, priority)
                    downloaded_files.add((file_name, priority))


def get_file_list(client_socket: socket.socket):
    client_socket.sendall("LIST".encode())
    file_list = client_socket.recv(1024).decode()
    print("File list:")
    print(file_list)


def main():
    host = "127.0.0.1"
    port = 10000
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    try:
        get_file_list(client_socket)
        monitor_input_file(client_socket)
    finally:
        client_socket.close()


if __name__ == "__main__":
    main()
