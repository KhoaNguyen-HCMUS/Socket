import os
import socket
import threading


def file_chunk_generator(file_path, chunk_size):
    #with open(file_path, "rb") as f:
    #   print(f.read())
    with open(file_path, "rb") as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            yield data


def send_file_list(client_socket: socket.socket):
    msg = client_socket.recv(1024).decode()
    if msg == "LIST":
        with open("files_list.txt", "r") as f:
            files_list = f.read()
        client_socket.sendall(files_list.encode())
    else:
        client_socket.sendall("Invalid command".encode())


SEPARATOR = " "


def handle_client(client_socket: socket.socket, file_list):
    send_file_list(client_socket)
    try:
        file_list_str = "\n".join(
            [
                f"{file_name}{SEPARATOR}{file_size}"
                for file_name, file_size, *_ in file_list
            ]
        )
        msg=client_socket.recv(1024).decode()
        if msg == "VALID_LIST":
            client_socket.sendall(file_list_str.encode()) #valid file list
            print ("valid file list sent")

        manager = {}

        while True:
            cmd = client_socket.recv(1024).decode()  # get
            if cmd == "get":
                #print("\n get")
                msg = client_socket.recv(1024).decode()
                if msg == "continue":
                    continue
                #print(msg)
                _, filename, priority_size = msg.split(SEPARATOR)[:3]
                print(_, filename, priority_size)

                chunk_sz = priority_size

                if filename not in manager:
                    file_path = os.path.join("Cloud", filename)
                    manager[filename] = file_chunk_generator(file_path, chunk_sz)

                chunk_data = next(manager[filename])
                print("len", len(chunk_data))

                client_socket.sendall(f"DATA{SEPARATOR}{filename}{SEPARATOR}{(chunk_data if chunk_data else "eof")}".encode())

            elif cmd == "terminated":
                break
    except:
        print("Error")
    finally:
        client_socket.close()


def main():
    host = "127.0.0.1"
    port = 10000
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print("Server listening on port", port)

    file_list = [
        (f, os.path.getsize(os.path.join("Cloud", f)), os.path.join("Cloud", f))
        for f in os.listdir("Cloud")
    ]

    while True:
        client_socket, addr = server_socket.accept()
        print("Connection from", addr)
        handle_client(client_socket, file_list)
        #threading.Thread(target=handle_client, args=(client_socket, file_list)).start()


if __name__ == "__main__":
    main()
