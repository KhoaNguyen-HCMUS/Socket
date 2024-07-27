import os
import socket
import sys
from time import sleep
import threading

available_files = {}
download_queue = {}
download_status = {}
files_not_found = []

def get_file_list(client_socket: socket.socket):
    client_socket.sendall("LIST".encode(FORMAT))
    lst = client_socket.recv(1024).decode(FORMAT)
    lst = lst.strip().split("\n")
    lst = [file.split(SEPARATOR) for file in lst]

    return [
        (file_name, int(file_size))
        for file_name, file_size in lst
    ]

def getStandardSize(size):
    itme=['B','KB','MB','GB','TB']
    for x in itme:
        if size < 1024.0:
            return  "%3.1f%s" % (size,x)
        size/=1024.0
    return size

def read_input_files():
    while True:
        with open("input.txt", "r") as f:
            input_files = f.read().strip().split("\n")
            input_files = [file.split(SEPARATOR) for file in input_files]
        
            for file in input_files:
                if file[0] not in available_files:
                    if file[0] in files_not_found:
                        continue
                    print(f"File {file[0]} not found.")
                    files_not_found.append(file[0])
                    continue
                
                #add already downloaded notifcation
                        
                priority_size = 1024
                if (len(file) > 1):
                    priority_size = get_priority_size(file[1])
                if file[0] not in download_queue:
                    download_queue[file[0]] = priority_size
                if file[0] not in download_status:
                    download_status[file[0]] = [priority_size, False]
                    with open(os.path.join("Output", file[0]), "wb") as f:
                        pass
        sleep(2)
        """ print("Download Queue:", download_queue)
        print("Download Status:", download_status) """

PRIOR_MAP = {"CRITICAL": 10, "HIGH": 4, "NORMAL": 1}

def get_priority_size(file_priority):
    return 1024 * PRIOR_MAP.get(file_priority, 1)

def write_file(file_name, data):
    with open(os.path.join("Output", file_name), "ab") as f:
        f.write(data)

def isAllDone(status):
    return all([status[1] for status in status.values()])

SEPARATOR = " "
FORMAT = "utf-8"

def client_request(client_socket: socket.socket):
    while True:
        client_socket.sendall("get".encode(FORMAT))
        download_status_copy = download_status.copy()
        
        try:
            while True:
                download_queue_copy = download_queue.copy()
                eliminate_files = []
                # print("Download Queue:", download_queue)
                # print("Download Status:", download_status)
                if  isAllDone(download_status_copy):
                    break
                
                for file_name, priority_size in download_queue_copy.items():
                    #print("send", file_name, priority_size)
                    client_socket.sendall(f"GET{SEPARATOR}{file_name}{SEPARATOR}{priority_size}".encode(FORMAT))
                    response = client_socket.recv(priority_size)

                    if response == b"EOF" or len(response) == 0 or not response:
                        eliminate_files.append(file_name)
                        download_status[file_name][1] = True 
                        print(download_status)
                    else :
                        if len(download_status[file_name]) < 3:
                            download_status[file_name].append(0)

                        download_status[file_name][2] += len(response)
                        write_file(file_name, response)
                    
                        current_size = os.path.getsize(os.path.join("Output", file_name))
                        if current_size >= available_files[file_name]:
                            download_status[file_name][1] = True 
                            print(f"File {file_name} downloaded.")
                            eliminate_files.append(file_name)

                download_queue_copy.clear()
                for file_name in eliminate_files:
                    if file_name in download_queue:
                        del download_queue[file_name]
            
            download_status_copy.clear()
            client_socket.sendall("done".encode(FORMAT))
        except Exception as e:
            print(f"Client request error: {e}")
            break

def main():
    host = "127.0.0.1"
    port = 65432

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    global file_list
    file_list = get_file_list(client_socket)

    for file_name, file_size in file_list:
        available_files[file_name] = file_size

    thread = threading.Thread(target=read_input_files)
    thread.start()
    
    sleep(0.25)

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
