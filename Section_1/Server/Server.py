import socket
import os
import customtkinter
import threading


class Server:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 10000
        self.server_socket = None
        self.text_widget = None  # Placeholder for the text widget
        self.server_running = False  # Flag to check if server is running

    def log_message(self, message):
        if self.text_widget:

            self.text_widget.insert(customtkinter.END, message + "\n")
            self.text_widget.see(customtkinter.END)
        print(message)

    def send_file_list(self, client_socket: socket.socket):
        message = client_socket.recv(1024).decode()
        if message == "list":
            self.handle_file_list(client_socket)
        else:
            self.log_message("Invalid message from client")

    def handle_file_list(self, client_socket: socket.socket):
        try:
            with open("files_list.txt", "r") as f:
                files_list = f.read()
            client_socket.sendall(files_list.encode())
            self.log_message("Sent file list to client.")
        except Exception as e:
            self.log_message(f"Error sending file list: {e}")

    def send_file(self, client_socket: socket.socket, file_name):
        try:
            server_py_directory = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(server_py_directory, "Cloud", file_name)
            with open(file_path, "rb") as f:
                file_size = os.path.getsize(file_path)
                client_socket.sendall(str(file_size).encode())
                bytes_sent = 0
                while bytes_sent < file_size:
                    data = f.read(1024)
                    client_socket.sendall(data)
                    bytes_sent += len(data)
            self.log_message(f"Sent file: {file_name}")
        except FileNotFoundError:
            client_socket.sendall("0".encode())
            self.log_message(f"File not found: {file_name}")
        except Exception as e:
            self.log_message(f"Error sending file {file_name}: {e}")

    def run(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(0)
            self.server_running = True
            self.log_message("Server started. Waiting for connection...")
            while self.server_running:
                client_socket, addr = self.server_socket.accept()
                client_socket.sendall("accepted".encode())
                self.log_message(f"Connection from {addr}")
                self.send_file_list(client_socket)
                try:
                    while True:
                        file_name = client_socket.recv(1024).decode()
                        if not file_name:
                            continue
                        self.send_file(client_socket, file_name)
                except Exception as e:
                    self.log_message(f"Error: {e}")
                finally:
                    client_socket.close()
                    self.log_message("Client connection closed.")
        except Exception as e:
            self.log_message(f"Server error: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
                self.log_message("Server socket closed.")

    def start_server(self):
        server_thread = threading.Thread(target=self.run)
        server_thread.daemon = True
        server_thread.start()

    def stop_server(self):
        self.server_running = False
        if self.server_socket:
            self.server_socket.close()
        self.log_message("Server stopped.")
        self.root.quit()

    def GUI(self):
        customtkinter.set_appearance_mode("Light")
        self.root = customtkinter.CTk()
        self.root.title("Server")
        self.root.geometry("500x500")
        self.root.resizable(True, True)

        self.text_widget = customtkinter.CTkTextbox(self.root, fg_color="#a9d6e5")
        self.text_widget.pack(expand=True, fill="both")

        stop_button = customtkinter.CTkButton(
            self.root,
            text="Stop Server",
            command=self.stop_server,
            fg_color="#1e3d59",
            text_color="#a9d6e5",
        )
        stop_button.pack(pady=10)

        self.start_server()  # Start the server in a separate thread
        self.root.mainloop()


if __name__ == "__main__":
    Server().GUI()
