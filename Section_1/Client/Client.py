import socket
import queue
import os


class Client:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 10000
        self.client_socket = None
        self.downloaded_files = set()

    def get_file_list(self):
        self.client_socket.sendall("list".encode())
        file_list = self.client_socket.recv(1024).decode()
        print("File list:")
        print(file_list)

    def get_new_files(self):
        with open("input.txt", "r") as f:
            current_files = f.read().splitlines()
        return [file for file in current_files if file not in self.downloaded_files]

    def request_file_download(self, file_name):
        self.client_socket.sendall(file_name.encode())
        # Assume the server sends the file size first
        file_size = int(self.client_socket.recv(1024).decode())
        if file_size:
            downloaded_size = 0  # Initialize the number of downloaded bytes
            with open(os.path.join("output", file_name), "wb") as f:
                while downloaded_size < file_size:
                    data = self.client_socket.recv(1024)
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

    def connect_to_server(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        return self.client_socket

    def run(self):
        self.downloaded_files = set()
        self.client_socket = self.connect_to_server()
        try:
            print("Connected to server.")
            self.get_file_list()
            while True:
                new_files = self.get_new_files()
                for file_name in new_files:
                    self.request_file_download(file_name)
                    self.downloaded_files.add(file_name)
        except ConnectionRefusedError:
            print("Connection refused. Server is not running.")
        except KeyboardInterrupt:
            print("\nClient is closing...")
            if self.client_socket:
                self.client_socket.close()
            print("Client closed.")
        except Exception as e:
            print(f"Error: {e}")
            if self.client_socket:
                self.client_socket.close()
        finally:
            if self.client_socket:
                self.client_socket.close()


if __name__ == "__main__":
    Client().run()
