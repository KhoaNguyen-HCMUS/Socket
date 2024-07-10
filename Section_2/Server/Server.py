import socket
import os
import threading

def send_file_list(client_socket):
    with open('files_list.txt', 'r') as f:
        files_list = f.read()
    client_socket.sendall(files_list.encode())

def send_file(client_socket, file_name):
    # Prepend the "Cloud" folder to the file_name
    server_py_directory = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(server_py_directory,'Cloud', file_name)
     # Initialize file_size
    file_size = None
    
    # Open files_list.txt and read file sizes
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        client_socket.sendall(str(file_size).encode())
        with open(file_path, 'rb') as f:
            bytes_sent = 0
            while bytes_sent < file_size:
                data = f.read(1024)
                client_socket.sendall(data)
                bytes_sent += len(data)
        print(f"Sent file: {file_name}")
    else:
        # Send a response indicating the file does not exist
        client_socket.sendall("0".encode())  # Indicating file size of 0 for non-existent file
        print(f"File {file_name} not found.")

def handle_client_connection(client_socket, addr):
    print(f"-----Connection from {addr}-----")
    try:
        while True:
            file_name = client_socket.recv(1024).decode()
            if not file_name:
                break
            send_file(client_socket, file_name)
    except socket.error as err:
        print(f"Socket error: {err}")
    except ConnectionError:
        print("Connection error")
    except TimeoutError:
        print("Timeout")
    finally:
        print(f"Client {addr} has disconnected.")
        client_socket.close()

def server():
    #host = '192.168.1.19' # Server IP address
    host = '127.0.0.1' #loopback address
    port = 10000
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #IPv4, TCP
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Server started on {host} port:{port}")
    print("Server is listening...")
    
    while True:
        client_socket, addr = server_socket.accept()
        client_thread = threading.Thread(target=handle_client_connection, args=(client_socket, addr))
        client_thread.start()

if __name__ == '__main__':
    server()