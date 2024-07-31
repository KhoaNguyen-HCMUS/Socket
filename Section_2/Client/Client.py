import os
import socket
import threading
from time import sleep
import customtkinter
from customtkinter import *

SEPARATOR = " "
FORMAT = "utf-8"
PRIOR_MAP = {"CRITICAL": 10, "HIGH": 4, "NORMAL": 1}
LINEBREAK = "----------------------------------------\n"


class Client:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 65432
        self.client_socket = None
        self.file_list = {}
        self.download_queue = {}
        self.download_status = {}
        self.files_not_found = []
        self.signal = threading.Event()

    def get_file_list(self):
        self.client_socket.sendall("LIST".encode(FORMAT))
        lst = self.client_socket.recv(1024).decode(FORMAT)
        lst = lst.strip().split("\n")
        lst = [file.split(SEPARATOR) for file in lst]

        print("File list:")
        for file_name, file_size in lst:
            self.file_list[file_name] = int(file_size)
            print(file_name, self.get_standard_size(int(file_size)))

    def get_standard_size(self, size):
        itme = ["B", "KB", "MB", "GB", "TB"]
        for x in itme:
            if size < 1024.0:
                return "%3.1f%s" % (size, x)
            size /= 1024.0
        return size

    def read_input_files(self):
        while not self.signal.is_set():
            with open("input.txt", "r") as f:
                input_files = f.read().strip().split("\n")
                input_files = [file.split(SEPARATOR) for file in input_files]

                for file in input_files:
                    if file[0] not in self.file_list:
                        if file[0] in self.files_not_found:
                            continue
                        print(f"{LINEBREAK}File {file[0]} not found.")
                        self.files_not_found.append(file[0])
                        continue

                    priority_size = 1024
                    if len(file) > 1:
                        priority_size = self.get_priority_size(file[1])
                    if file[0] not in self.download_status:
                        self.download_status[file[0]] = [priority_size, False]
                        self.download_queue[file[0]] = priority_size
                        with open (os.path.join("Output", file[0]), "wb") as f:
                            pass
            sleep(2)

    def get_priority_size(self, file_priority):
        return 1024 * PRIOR_MAP.get(file_priority, 1)

    def write_file(self, file_name, data):
        with open (os.path.join("Output", file_name), "ab") as f:
            f.write(data)

    def is_all_done(self, status):
        return all([status[1] for status in status.values()])

    def client_request(self):
        while not self.signal.is_set():
            self.client_socket.sendall("get".encode(FORMAT))
            download_status_copy = self.download_status.copy()

            try:
                while not self.signal.is_set():
                    download_queue_copy = self.download_queue.copy()
                    eliminate_files = []

                    if self.is_all_done(download_status_copy):
                        break

                    for file_name, priority_size in download_queue_copy.items():
                        # if file_name in self.download_status:
                        #     if self.download_status[file_name][1]:
                        #         print(f"File {file_name} already downloaded.")
                        #         continue
                        self.client_socket.sendall(
                            f"GET{SEPARATOR}{file_name}{SEPARATOR}{priority_size}".encode(
                                FORMAT
                            )
                        )
                        response = self.client_socket.recv(priority_size)

                        if response == b"EOF" or len(response) == 0 or not response:
                            eliminate_files.append(file_name)
                            self.download_status[file_name][1] = True
                        else:
                            if len(self.download_status[file_name]) < 3:
                                self.download_status[file_name].append(0)

                            #self.download_status[file_name][2] += len(response)
                            self.write_file(file_name, response)

                            current_size = os.path.getsize(
                                os.path.join("Output", file_name)
                            )
                            if current_size >= self.file_list[file_name]:
                                self.download_status[file_name][1] = True
                                print(f"{LINEBREAK}Downloaded file {file_name} successfully.")
                                eliminate_files.append(file_name)

                    download_queue_copy.clear()
                    for file_name in eliminate_files:
                        if file_name in self.download_queue:
                            del self.download_queue[file_name]

                download_status_copy.clear()
                self.client_socket.sendall("done".encode(FORMAT))
            except Exception:
                self.signal.set()
                print(
                    "Error: Server interrupted, connection was forcibly closed by the remote host."
                )
                self.client_socket.close()
                print("Client closed.")
                break

    def start(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))

            self.get_file_list()

            thread = threading.Thread(target=self.read_input_files)
            thread.start()

            sleep(0.25)
            self.client_request()
        except KeyboardInterrupt:
            self.signal.set()
            self.client_socket.sendall("terminate".encode(FORMAT))
            print("\nClient is closing...")
            print("Client closed.")
        except ConnectionRefusedError:
            print("Connection refused. Server not responding.")
            print("Client closed.")
        except Exception as e:
            print(
                "Error: Server interrupted, connection was forcibly closed by the remote host."
            )
            print("Client closed.")
        finally:
            self.signal.set()
            self.client_socket.close()


if __name__ == "__main__":
    client = Client()
    client.start()
