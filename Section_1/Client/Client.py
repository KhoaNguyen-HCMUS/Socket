import socket
import os
import customtkinter
import threading

class Client:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 10000
        self.client_socket = None
        self.downloaded_files = set()
        self.text_widget = None  # Placeholder for the text widget
        self.client_running = False  # Flag to check if server is running
        self.root = customtkinter.CTk()

    def log_message(self, message):
        if self.text_widget:
            self.text_widget.insert(customtkinter.END, message + "\n")
            self.text_widget.see(customtkinter.END)
        print(message)

    def get_file_list(self):
        self.client_socket.sendall("list".encode())
        file_list = self.client_socket.recv(1024).decode()
        self.log_message("File list:")
        self.log_message(file_list)

    def get_new_files(self):
        with open("input.txt", "r") as f:
            current_files = f.read().splitlines()
        return [file for file in current_files if file not in self.downloaded_files]

    def request_file_download(self, file_name):
        self.client_socket.sendall(file_name.encode())
        # Assume the server sends the file size first
        file_size = int(self.client_socket.recv(1024).decode())

        frame = customtkinter.CTkFrame(self.root)
        labelPercentage = customtkinter.CTkLabel(frame, text=f"Downloading {file_name}: 0.00% completed")
        labelPercentage.pack()
        frame.pack()

        if file_size:
            downloaded_size = 0  # Initialize the number of downloaded bytes
            with open(os.path.join("output", file_name), "wb") as f:
                while downloaded_size < file_size:
                    data = self.client_socket.recv(1024)
                    f.write(data)
                    downloaded_size += len(data)
                    # Calculate and display progress percentage
                    progress_percentage = (downloaded_size / file_size) * 100
                    print(
                        f"Downloading {file_name}: {progress_percentage:.2f}% completed",
                        end="\r",
                    )
                    labelPercentage.config(text=f"Downloading {file_name}: {progress_percentage:.2f}% completed")
            self.log_message(f"\nDownloaded {file_name}")
            self.log_message(f"\n-------------")
        else:
            self.log_message(f"File {file_name} not found on server\n-------------")

    def connect_to_server(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))
        return self.client_socket

    def run(self):
        self.downloaded_files = set()
        self.client_socket = self.connect_to_server()
        try:
            self.log_message("Connected to server.")
            self.get_file_list()
            while not self.client_running:
                new_files = self.get_new_files()
                for file_name in new_files:
                    if file_name not in self.downloaded_files:
                        self.request_file_download(file_name)
                        self.downloaded_files.add(file_name)
        except ConnectionRefusedError:
            self.log_message("Connection refused. Server is not running.")
        except KeyboardInterrupt:
            self.log_message("\nClient is closing...")
            if self.client_socket:
                self.client_socket.close()
            self.log_message("Client closed.")
        except Exception as e:
            self.log_message(f"Error: {e}")
            if self.client_socket:
                self.client_socket.close()
        finally:
            if self.client_socket:
                self.client_socket.close()

    def start_client(self):
        client_thread = threading.Thread(target=self.run)
        client_thread.daemon = True
        client_thread.start()

    def stop_client(self):
        self.client_running = False
        if self.client_socket:
            self.client_socket.close()
        self.log_message("Client stopped.")
        self.root.quit()

    def GUI(self):
        self.root = customtkinter.CTk()
        self.root.title("Client")
        self.root.geometry("500x500")
        self.text_widget = customtkinter.CTkTextbox(self.root, fg_color="#a9d6e5")
        self.text_widget.pack(fill="both", expand=True)
        stop_button = customtkinter.CTkButton(
            self.root,
            text="Stop Client",
            command=self.stop_client,
            fg_color="#1e3d59",
            text_color="#a9d6e5",
        )
        stop_button.pack()

        self.start_client()
        self.root.mainloop()


if __name__ == "__main__":
    Client().GUI()
