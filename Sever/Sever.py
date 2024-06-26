import socket
import os

def send_file_list(client_socket):
    with open('files_list.txt', 'r') as f:
        files_list = f.read()
    client_socket.sendall(files_list.encode())

def send_file(client_socket, file_name):
    if os.path.isfile(file_name):
        file_size = os.path.getsize(file_name)
        client_socket.sendall(f"{file_size}".encode())
        with open(file_name, 'rb') as f:
            data = f.read()
            client_socket.sendall(data)
    else:
        client_socket.sendall(b'0')

def server():
    host = 'localhost'
    port = 12345
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print("Server is listening...")
    
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        send_file_list(client_socket)
        
        while True:
            file_name = client_socket.recv(1024).decode()
            if not file_name:
                break
            send_file(client_socket, file_name)
        
        client_socket.close()

if __name__ == '__main__':
    server()