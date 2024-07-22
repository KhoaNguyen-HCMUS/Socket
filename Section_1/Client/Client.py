import socket
import time
import os


def get_file_list(client_socket):
    client_socket.sendall("list".encode())
    file_list = client_socket.recv(1024).decode()
    print("File list:")
    print(file_list)


def get_new_files(downloaded_files):
    with open("input.txt", "r") as f:
        current_files = f.read().splitlines()
    return [file for file in current_files if file not in downloaded_files]


def connect_to_server():
    # host = '192.168.1.19' # Server IP address
    host = "127.0.0.1"  # loopback address
    port = 10000
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    return client_socket


def request_file_download(client_socket, file_name):
    client_socket.sendall(file_name.encode())
    # Assume the server sends the file size first
    file_size = int(client_socket.recv(1024).decode())
    if file_size:
        downloaded_size = 0  # Initialize the number of downloaded bytes
        with open(os.path.join("output", file_name), "wb") as f:
            while downloaded_size < file_size:
                data = client_socket.recv(1024)
                f.write(data)
                downloaded_size += len(data)
                # Calculate and display progress percentage
                progress_percentage = (downloaded_size / file_size) * 100
                print(
                    f"Downloading {file_name}: {progress_percentage:.2f}% complete",
                    end="\r",
                )
        print(f"\n-------------")
    else:
        print(f"File {file_name} not found on server\n-------------")


def main():
    downloaded_files = set()
    client_socket = connect_to_server()

    try:
        print("Connected to server.")
        print("Client address:", client_socket.getsockname())
        get_file_list(client_socket)
        while True:
            new_files = set(get_new_files(downloaded_files))  # Convert to set to remove duplicates
            for file_name in new_files:
                request_file_download(client_socket, file_name)
                downloaded_files.add(file_name)

    except ConnectionRefusedError:
        print("Can't connect to server. Please check IP address and port again.")
    except Exception as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("Client is shutting down.")
    finally:
        client_socket.close()


if __name__ == "__main__":
    main()
