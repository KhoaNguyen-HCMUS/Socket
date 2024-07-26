import os
import socket
import sys

def get_file_list(client_socket: socket.socket):
    client_socket.sendall("LIST".encode())
    file_list = client_socket.recv(1024).decode()
    for file in file_list.strip().split("\n"):
        file_name, file_size = file.split(SEPARATOR)
        print(file_name + " " + getStandardSize(int(file_size)))

def getStandardSize(size):
    itme=['B','KB','MB','GB','TB']
    for x in itme:
        if size < 1024.0:
            return  "%3.1f%s" % (size,x)
        size/=1024.0
    return size

def read_input_files():
    with open("input.txt", "r") as f:
        input_files = f.read().split("\n")
        input_files = [file.split(SEPARATOR) for file in input_files]

    return [
        (file_name, get_priority_size(file_priority))
        for file_name, file_priority in input_files
    ]

PRIOR_MAP = {"CRITICAL": 10, "HIGH": 4, "LOW": 1}

def get_priority_size(file_priority):
    return 1024 * PRIOR_MAP.get(file_priority, 1)

def write_file(file_name, data):
    with open(os.path.join("Output", file_name), "ab") as f:
        f.write(data)

SEPARATOR = " "

def monitor_input_file(client_socket: socket.socket):
    pass

def client_request(client_socket: socket.socket):
    get_file_list(client_socket)
    input_files = read_input_files(input_files)
    

def main():
    host = "127.0.0.1"
    port = 65432

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    client_socket.connect((host, port))

    try: 
        client_request(client_socket)

    except KeyboardInterrupt:
        print("\nClient is closing...")
        client_socket.close()
        print("Client closed.")
    except ConnectionRefusedError:
        print("Connection refused. Server not responding.")
    except Exception as e:
        print(f"Error: {e}")
        if client_socket:
            client_socket.close()
    finally:
        client_socket.close()

if __name__ == "__main__":
    main()
