import os
import socket
import customtkinter
import threading

SEPARATOR = " "
FORMAT = "utf-8"
LINEBREAK = "----------------------------------------\n"


class Server:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 65432
        self.server_socket = None
        self.socket_list = {}
        self.text_widget = None  # Placeholder for the text widget

    def log_message(self, message):
        if self.text_widget:

            self.text_widget.insert(customtkinter.END, message + "\n")
            self.text_widget.see(customtkinter.END)
        print(message)

    def gen_file_list(self, file_path):
        with open(file_path, "w") as f:
            for file_name in os.listdir("Cloud"):
                f.write(
                    f'{file_name}{SEPARATOR}{str(os.path.getsize(os.path.join("Cloud", file_name)))}\n'
                )

    def send_file_list(self, client_socket: socket.socket):
        msg = client_socket.recv(1024).decode(FORMAT)
        if msg == "LIST":
            with open("file_list.txt", "r") as f:
                file_list = f.read()
            client_socket.sendall(file_list.encode(FORMAT))
        else:
            self.log_message("\nInvalid command.")

    def file_chunk_generator(self, file_path, chunk_size):
        with open(file_path, "rb") as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    yield b"EOF"
                    break
                yield data

    def handle_client(self, client_socket: socket.socket, addr):
        self.send_file_list(client_socket)
        download_manager = {}
        try:
            while True:
                cmd = client_socket.recv(1024).decode(FORMAT)
                if cmd == "get":
                    while True:
                        request = client_socket.recv(1024).decode(FORMAT)
                        if request[:4] == "done":
                            break
                        if request[:9] == "terminate":
                            client_socket.close()
                            self.log_message(f"{LINEBREAK}Client {addr} disconnected.")
                            return

                        _, file_name, priority_size = request.split(SEPARATOR)
                        self.send_data(
                            client_socket,
                            file_name,
                            int(priority_size),
                            download_manager,
                        )
                elif cmd == "terminate":
                    client_socket.close()
                    self.log_message(f"{LINEBREAK}Client {addr} disconnected.")
                    break
        except Exception:
            self.log_message(
                f"{LINEBREAK}Error: Client {self.socket_list[client_socket]} was forcibly closed by the remote host."
            )
            client_socket.close()

    def send_data(
        self, client_socket: socket.socket, file_name, priority_size, download_manager
    ):
        file_path = os.path.join("Cloud", file_name)
        chunk_size = priority_size

        if file_name not in download_manager:
            download_manager[file_name] = self.file_chunk_generator(
                file_path, chunk_size
            )
        try:
            data = next(download_manager[file_name])
            client_socket.sendall(data)
        except StopIteration:
            del download_manager[file_name]

    def process(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            self.socket_list[client_socket] = addr
            self.log_message(f"{LINEBREAK}Client {addr} connected.")
            client_thread = threading.Thread(
                target=self.handle_client, args=(client_socket, addr)
            )
            client_thread.start()

    def run(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

        self.log_message("Server started. Waiting for connection...")

        self.gen_file_list("file_list.txt")

        process_thread = threading.Thread(target=self.process)
        process_thread.start()

    def stop_server(self):
        self.server_socket.close()
        self.log_message("Server stopped.")
        self.root.quit()

    def start_server(self):
        server_thread = threading.Thread(target=self.run)
        server_thread.daemon = True
        server_thread.start()

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
