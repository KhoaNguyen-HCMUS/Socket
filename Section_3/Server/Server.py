import os
import socket
import threading

def gen_file_list(file_path):
    with open(file_path, "w") as f:
        for file_name in os.listdir("Cloud"):
            f.write(f'{file_name}{SEPARATOR}{str(os.path.getsize(os.path.join("Cloud", file_name)))}\n')

def send_file_list(client_socket: socket.socket):
    msg = client_socket.recv(1024).decode()
    if msg == "LIST":
        with open("file_list.txt", "r") as f:
            file_list = f.read()
        client_socket.sendall(file_list.encode())
    else:
        print("\nInvalid command.")

def file_chunk_generator(file_path, chunk_size):
    # with open(file_path, "rb") as f:
    #   print(f.read())
    with open(file_path, "rb") as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            yield data

SEPARATOR = " "

def handle_client(client_socket: socket.socket):
    send_file_list(client_socket)

def main():
    host = "127.0.0.1"
    port = 65432

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.bind((host, port))
    server_socket.listen(5)

    print("Server listening on port", port)

    gen_file_list("file_list.txt")

    while True:
        client_socket, addr = server_socket.accept()
        print("Connection from", addr)
        handle_client(client_socket)
        #handle_client(client_socket, file_list)
        #threading.Thread(target=handle_client, args=(client_socket, file_list)).start()

if __name__ == "__main__":
    main()
