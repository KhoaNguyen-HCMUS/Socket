import os
import socket
import threading

manager = {}

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

def file_chunk_generator(file_path, chunk_size):
    # with open(file_path, "rb") as f:
    #   print(f.read())
    with open(file_path, "rb") as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                yield b"EOF"
                break
            yield data

SEPARATOR = " "
FORMAT = "utf-8"

def handle_client(client_socket: socket.socket):
    send_file_list(client_socket)
    
    while True:
        cmd = client_socket.recv(1024).decode(FORMAT)
        if cmd == "get":
            while True:
                request = client_socket.recv(1024).decode(FORMAT)
                if request[:4] == "done":
                    break
                #print(request, len(request))

                _, file_name, priority_size = request.split(SEPARATOR)
                #print (file_name, priority_size)

                download_manager(client_socket, file_name, int(priority_size))
        elif cmd == "success":
            pass

def download_manager(client_socket: socket.socket, file_name, priority_size):
    file_path = os.path.join("Cloud", file_name)
    chunk_size = priority_size

    if file_name not in manager:
        manager[file_name] = file_chunk_generator(file_path, chunk_size)
    try:
        data = next(manager[file_name])
        client_socket.sendall(data)
    except StopIteration:
        del manager[file_name]

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
        #threading.Thread(target=handle_client, args=(client_socket, file_list)).start()

if __name__ == "__main__":
    main()
