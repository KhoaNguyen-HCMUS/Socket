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
        self.files_list_path = "files_list.txt"

    def log_message(self, message):
        if self.text_widget:

            self.text_widget.insert(customtkinter.END, message + "\n")
            self.text_widget.see(customtkinter.END)
        print(message)

    def gen_file_list(self):
        try:
            with open(self.files_list_path, "w") as f:
                for file_name in os.listdir("Cloud"):
                    file_path = os.path.join("Cloud", file_name)
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        f.write(f"{file_name} {file_size}\n")
        except Exception as e:
            self.log_message(f"An error occurred while updating files_list.txt: {e}")

    def send_file_list(self, client_socket: socket.socket):
        message = client_socket.recv(1024).decode()
        if message == "list":
            try:
                with open(self.files_list_path, "r") as f:
                    files_list = f.read()
                client_socket.sendall(files_list.encode())
                self.log_message("Sent file list to client.")
            except Exception as e:
                self.log_message(f"Error sending file list: {e}")
        else:
            self.log_message("Invalid message from client")
    

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
            self.server_socket.listen()
            self.server_running = True
            self.gen_file_list()
            self.log_message("Server started. Waiting for connection...")
            while self.server_running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    client_socket.sendall("accepted".encode())
                    self.log_message(f"Connection from {addr}")
                    self.send_file_list(client_socket)
                    while True:
                        file_name = client_socket.recv(1024).decode()
                        if file_name == "close":
                            client_socket.close()
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
        self.root = customtkinter.CTk()
        self.root.title("Server")
        self.root.geometry("600x600")  # Increased window size
        self.root.resizable(True, True)
        self.root.configure(bg="#34568B")  # Set a background color

        # Header
        header = customtkinter.CTkLabel(
            self.root,
            text="Server Control Panel",
            font=("Arial", 20),
            fg_color="#34568B",
            text_color="white",
            corner_radius=10,
        )
        header.pack(pady=10)

        self.text_widget = customtkinter.CTkTextbox(
            self.root, fg_color="#a9d6e5", font=("Arial", 14), width=120, height=10
        )
        self.text_widget.pack(expand=True, fill="both", padx=10, pady=10)

        stop_button = customtkinter.CTkButton(
            self.root,
            text="Stop Server",
            command=self.stop_server,
            fg_color="#FF6F61",  # Button color
            text_color="white",  # Text color
            font=("Arial", 16),  # Font size
            width=120,  # Button width
            height=50,  # Button height
            corner_radius=10,  # Rounded corners
        )
        stop_button.pack(pady=20)

        self.start_server()  # Start the server in a separate thread
        self.root.mainloop()


if __name__ == "__main__":
    Server().GUI()
