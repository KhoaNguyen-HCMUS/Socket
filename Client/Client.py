import queue
import socket
import time
import os

def request_file_download(file_name):
    host = 'localhost'
    port = 12345
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    
    files_list = client_socket.recv(1024).decode()
    
    client_socket.sendall(file_name.encode())
    
    file_size = int(client_socket.recv(1024).decode())
    if file_size > 0:
        with open(f"output/{file_name}", 'wb') as f:
            received = 0
            while received < file_size:
                data = client_socket.recv(1024)
                if not data:
                    break
                f.write(data)
                received += len(data)
                print(f"Downloading {file_name}: {received * 100 / file_size:.2f}%")
    
    else :
        print(f"File {file_name} not found")
    client_socket.close()

def client():
    downloaded_files = set()
    files_to_download = queue.Queue()

    while True:
        with open('input.txt', 'r') as f:
            for file_name in f.read().splitlines():
                if file_name not in downloaded_files:
                    files_to_download.put(file_name)
        
        while not files_to_download.empty():
            file_name = files_to_download.get()
            request_file_download(file_name)
            downloaded_files.add(file_name)
        
        time.sleep(2)

if __name__ == '__main__':
    client()