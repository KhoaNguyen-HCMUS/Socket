import os
import socket
import sys
import time


# def read_input_file():
#     with open("input.txt", "r") as file:
#         return [tuple(line.strip().split(",")) for line in file.readlines()]

PRIOR_MAP = {"CRITICAL": 10, "HIGH": 4, "LOW": 1}


def get_priority_size(file_priority):
    return 1024 * PRIOR_MAP.get(file_priority, 1)


def get_input_files():
    with open("input.txt", "r") as f:
        input_file_list_origin = f.read().splitlines()
        input_file_list_origin = [file.split(" ") for file in input_file_list_origin]

    return [
        (file_name, get_priority_size(file_priority))
        for file_name, file_priority in input_file_list_origin
    ]


def write_file(file_name, data):
    with open(os.path.join("Output", file_name), "ab") as f:
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
    pass


SEPARATOR = " "


def monitor_input_file(client_socket: socket.socket):
    client_socket.sendall("VALID_LIST".encode())
    raw_valid_files = client_socket.recv(1024).decode()
    valid_files: dict = {}

    for file in raw_valid_files.split("\n"):
        file_name, file_size = file.split(SEPARATOR)
        file_size = int(file_size)

        valid_files[file_name] = file_size

    input_files = set(get_input_files())
    num_input_files = len(input_files)

    downloaded_files = set()
    num_downloaded_files = 0

    downloader = {}

    print("input", input_files)
    print("valid", valid_files)

    print("Monitoring input files...")
    #while True:
    client_socket.sendall("get".encode())

    for file_name, priority_size in input_files:
        if file_name in valid_files and file_name not in downloaded_files:
            print("send", file_name, priority_size)
            client_socket.sendall(f"GET{SEPARATOR}{file_name}{SEPARATOR}{priority_size}".encode())
            
            # receive data
            data = client_socket.recv(1024).decode()
            print("recv", data)
            _, filename, chunk_data = data.split(SEPARATOR)
            #_, filename, chunk_data = "", "", b""
            print(_, filename, chunk_data)
            # process data, if data is eof, then update downloaded_files
            if chunk_data == "eof":
                downloaded_files.add(file_name)
                num_downloaded_files += 1
            else:
                write_file(file_name, chunk_data)

            #if num_downloaded_files == num_input_files:
                #break
            client_socket.sendall("get".encode())
        else:
            print(f"File {file_name} not found")
            client_socket.sendall("continue".encode())
            client_socket.sendall("get".encode())
        if num_downloaded_files == num_input_files:
            break

        # input_files.update(get_input_files())s


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
    except ConnectionRefusedError:
        print("Connection refused. Server is not running.")
    except KeyboardInterrupt:
        print("\nClient is closing...")
        client_socket.close()
        print("Client closed.")
    except Exception as e:
        print(f"Error: {e}")
        if client_socket:
            client_socket.close()
    finally:
        client_socket.close()


if __name__ == "__main__":
    main()
