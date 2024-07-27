import socket
import threading
import os
from time import sleep

FORMAT = "utf-8"
SEPARATOR = " "
SIGNAL = threading.Event()

downloaded_files = []
download_queue = {}
file_list = {}

def get_file_list(client_socket: socket.socket):
	client_socket.sendall("LIST".encode(FORMAT))
	lst = client_socket.recv(1024).decode(FORMAT)
	lst = lst.strip().split("\n")
	lst = [file.split(SEPARATOR) for file in lst]
	
	print("File list:")
	for file in lst:
		file_list[file[0]] = int(file[1])
		print(file[0], getStandardSize(int(file[1])))

def getStandardSize(size):
	itme=['B','KB','MB','GB','TB']
	for x in itme:
		if size < 1024.0:
			return  "%3.1f%s" % (size,x)
		size/=1024.0
	return size

def read_input_files():
	while not SIGNAL.is_set():
		with open("input.txt", "r") as f:
			input_files = f.read().strip().split("\n")
			input_files = [file.split(SEPARATOR) for file in input_files]
			
			for file in input_files:
				if file[0] not in file_list:
					#print(f"File {file[0]} not found.")
					continue
				if file[0] in downloaded_files and file[0] not in download_queue:
					#print(f"File {file[0]} already downloaded.")
					continue
				if file[0] not in download_queue:
					with open(os.path.join("Output", file[0]), "wb") as f:
						pass
		sleep(2)

def write_file(file_name, data):
	with open(os.path.join("Output", file_name), "ab") as f:
		f.write(data)

def client_request(client_socket: socket.socket):
	get_file_list(client_socket)
	while not SIGNAL.is_set():
		client_socket.sendall("get".encode(FORMAT))
	