import socket
import os

def send_file_list(client_socket):
    with open('files_list.txt', 'r') as f:
        files_list = f.read()
    client_socket.sendall(files_list.encode())

def send_file(client_socket, file_name):
    # Prepend the "Cloud" folder to the file_name
    file_path = os.path.join("Cloud", file_name)
    
    # Check if the file exists
    if os.path.isfile(file_path):
        # Assuming you have a way to send the file size first
        file_size = os.path.getsize(file_path)
        client_socket.sendall(str(file_size).encode())
        
        with open(file_path, 'rb') as f:
            bytes_sent = 0
            while bytes_sent < file_size:
                data = f.read(1024)
                client_socket.sendall(data)
                bytes_sent += len(data)
        print(f"File {file_name} sent successfully.")
    else:
        print(f"File {file_name} not found.")
        # Optionally, send a message to the client indicating the file was not found
        client_socket.sendall("File not found".encode())

def server():
    host = '192.168.1.10'
    port = 10000
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #IPv4, TCP
    server_socket.bind((host, port))
    server_socket.listen(5)
    print("Server is listening...")
    
    while True:
        client_socket, addr = server_socket.accept()
        print(f"-----Connection from {addr}-----")
        try:
            while True:
                file_name = client_socket.recv(1024).decode()
                if not file_name:
                    break
                send_file(client_socket, file_name)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            client_socket.close()

if __name__ == '__main__':
    server()