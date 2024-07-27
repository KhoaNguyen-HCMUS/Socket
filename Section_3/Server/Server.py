import socket
import threading
import os

FORMAT = "utf-8"
SEPARATOR = " "
SIGNAL = threading.Event()

def gen_file_list(file_path):
    with open(file_path, "w") as f:
        for file_name in os.listdir("Cloud"):
            f.write(f'{file_name}{SEPARATOR}{str(os.path.getsize(os.path.join("Cloud", file_name)))}\n')

def send_file_list(client_socket: socket.socket):
    msg = client_socket.recv(1024).decode(FORMAT)
    if msg == "LIST":
        with open("file_list.txt", "r") as f:
            file_list = f.read()
        client_socket.sendall(file_list.encode(FORMAT))
    else:
        print("\nInvalid command.")
        
def handle_client(client_socket: socket.socket, addr):
    send_file_list(client_socket)
    

def send_data(client_socket: socket.socket, file_name, file_size):
    pass

def process(server_socket: socket.socket):
    while not SIGNAL.is_set():
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr} has been established.")
        t = threading.Thread(target=handle_client, args=(client_socket, addr))
        t.start()

def main():
    host = "127.0.0.1"
    port = 65432
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)

    print(f"Server started. Listening on {host}:{port}")

    gen_file_list("file_list.txt")

    try:
        t = threading.Thread(target=process, args=(server_socket,))
        t.start()
        while not SIGNAL.is_set():
            pass
    except KeyboardInterrupt:
        print("\nServer shutting down.")
        SIGNAL.set()
        t.join()
        server_socket.close()
        print("Server closed.")
    finally:
        server_socket.close()

