import socket
import os
import customtkinter
import threading
import time
from customtkinter import *
import math

LINEBREAK = "-" * 20


class Client:

    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 10000
        self.client_socket = None
        self.downloaded_files = set()
        self.text_widget = None  # Placeholder for the text widget
        self.client_running = False  # Flag to check if server is running
        self.root = customtkinter.CTk()
        self.file_list_from_server = []
        self.is_connected = False

        # Create a CTkLabel to display the progress percentage
        self.progress_label = customtkinter.CTkLabel(
            self.root, text="Download progress: 0%"
        )
        self.progress_label.pack(pady=10)

        # Create a CTkProgressBar to display the download progress
        self.progress_bar = customtkinter.CTkProgressBar(self.root)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)  # Set the initial value of the progress bar to 0

    def log_message(self, message):
        if self.text_widget:
            self.text_widget.insert(customtkinter.END, message + "\n")
            self.text_widget.see(customtkinter.END)
        print(message)

    def get_file_list(self):
        self.client_socket.sendall("list".encode())
        file_list_str = self.client_socket.recv(1024).decode()
        file_list = file_list_str.strip().split("\n")
        file_names = []
        processed_files = []

        # Function to convert file size to human-readable format
        def convert_size(size_bytes):
            if size_bytes == 0:
                return "0B"
            size_name = ("B", "KB", "MB", "GB", "TB")
            i = int(math.floor(math.log(size_bytes, 1024)))
            p = math.pow(1024, i)
            s = round(size_bytes / p, 2)
            return f"{s} {size_name[i]}"

        for file in file_list:
            name, size = file.split(" ")
            size = int(size)
            readable_size = convert_size(size)
            file_names.append(name)
            processed_files.append(f"{name} - {readable_size}")

        self.file_list_from_server = file_names
        self.log_message(
            f"FILES AVAILABLE ON SERVER:\n{'\n'.join(processed_files)}\n{LINEBREAK}"
        )

    def get_new_files(self):
        with open("input.txt", "r") as f:
            current_files = f.read().splitlines()
        return current_files

    def request_file_download(self, file_name, count_appear):
        if file_name in self.downloaded_files:
            self.log_message(
                f"File {file_name} has already been downloaded.\n {LINEBREAK}"
            )
            return
        self.client_socket.sendall(file_name.encode())
        # Assume the server sends the file size first
        file_size = int(self.client_socket.recv(1024).decode())
        if file_size:
            downloaded_size = 0  # Initialize the number of downloaded bytes
            with open(os.path.join("output", file_name), "wb") as f:
                while downloaded_size < file_size:
                    data = self.client_socket.recv(1024)
                    f.write(data)
                    downloaded_size += len(data)
                    # Calculate and display progress percentage
                    progress_percentage = (downloaded_size / file_size) * 100

                    # Upadte CTkLabel to display the progress percentage
                    self.progress_label.configure(
                        text=f"Download {file_name} progress: {progress_percentage:.2f}%"
                    )
                    self.root.update()  # Update the GUI to reflect the changes

                    # Update the CTkProgressBar to display the download progress
                    self.progress_bar.set(downloaded_size / file_size)
                    self.root.update()
            self.log_message(f"Download {file_name} successful\n{LINEBREAK}")

        else:
            (
                self.log_message(f"File {file_name} not found on server\n{LINEBREAK}")
                if (count_appear[file_name] == 0)
                else None
            )

    def run(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            self.client_socket.settimeout(5.0)  # Set a timeout of 5 seconds
            try:
                self.log_message("Waiting for server response in 5 seconds...")
                msg = self.client_socket.recv(1024).decode()
            except socket.timeout:
                self.log_message(
                    "Connection refused. Server is not running. Please stop client and try again later."
                )
                # self.client_socket.close()
                return
            self.client_socket.settimeout(None)  # Disable the timeout
            self.is_connected = True
            self.log_message("Connected to server")
            self.get_file_list()
            count_appear = {}
            file_proccessed_count = 0
            while not self.client_running:
                new_files = self.get_new_files()
                if len(new_files) > file_proccessed_count:
                    if (
                        new_files[file_proccessed_count]
                        not in self.file_list_from_server
                    ):
                        self.log_message(
                            f"{new_files[file_proccessed_count]} is not found on Server\n{LINEBREAK}"
                        )
                    elif new_files[file_proccessed_count] in self.downloaded_files:
                        self.log_message(
                            f"{new_files[file_proccessed_count]} is already downloaded\n{LINEBREAK}"
                        )
                    else:
                        self.request_file_download(
                            new_files[file_proccessed_count], count_appear
                        )
                        print(new_files[file_proccessed_count])
                        self.downloaded_files.add(new_files[file_proccessed_count])
                    file_proccessed_count += 1
                else:
                    self.log_message("No new files to download\n")
                    self.log_message("Stop Client in 5 seconds...\n")
                    time.sleep(5)
                    self.stop_client()
                    break

        except KeyboardInterrupt:
            self.log_message("Client is closing...")
            if self.client_socket:
                self.client_socket.close()
            self.log_message("Client closed.")
        except ConnectionAbortedError:
            self.log_message(
                "Connection aborted. Server is not running. Please stop client and try again later."
            )
            self.client_socket.close()
        except ConnectionRefusedError:
            self.log_message(
                "Connection refused. Server is not running. Please stop client and try again later."
            )
            self.client_socket.close()
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
        if self.is_connected:
            self.client_socket.sendall("close".encode())
            self.client_socket.close()
        self.log_message("Client stopped.")
        self.root.quit()

    def input_file_name(self):
        file_name = self.file_input_textbox.get("1.0", "end-1c").strip()
        with open("input.txt", "a") as f:
            f.write("\n" + file_name)

    def clear_placeholder(self, event):
        if (
            self.file_input_textbox.get("1.0", "end-1c")
            == "Enter file name, e.g., input.txt"
        ):
            self.file_input_textbox.delete("1.0", "end")

    def add_placeholder(self, event):
        if not self.file_input_textbox.get("1.0", "end-1c"):
            self.file_input_textbox.insert("1.0", "Enter file name, e.g., input.txt")

    def GUI(self):
        self.root = customtkinter.CTk()
        self.root.title("Client")
        self.root.geometry("600x600")
        self.root.resizable(True, True)
        self.root.configure(bg="#34568B")
        header = customtkinter.CTkLabel(
            self.root,
            text="Client Control Panel",
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

        self.progress_label = customtkinter.CTkLabel(
            self.root, text="Download progress: 0%"
        )
        self.progress_label.pack(pady=10)
        self.progress_bar = customtkinter.CTkProgressBar(self.root)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)

        # Add file input entry
        self.file_input_textbox = customtkinter.CTkTextbox(
            self.root,
            width=200,
            height=100,
            fg_color="white",
            text_color="black",
        )
        self.file_input_textbox.insert("1.0", "Enter file name, e.g., input.txt")
        self.file_input_textbox.bind("<FocusIn>", self.clear_placeholder)
        self.file_input_textbox.bind("<FocusOut>", self.add_placeholder)
        self.file_input_textbox.pack(pady=10)

        # Step 3: Add a Submit Button for the file input
        submit_button = customtkinter.CTkButton(
            self.root,
            text="Enter",
            command=self.input_file_name,  # This method will handle the file input
            fg_color="#007BFF",  # Button color
            text_color="white",  # Text color
            font=("Arial", 16),  # Font size
        )
        submit_button.pack(pady=10)

        stop_button = customtkinter.CTkButton(
            self.root,
            text="Stop Client",
            command=self.stop_client,
            fg_color="#FF6F61",  # Button color
            text_color="white",  # Text color
            font=("Arial", 16),  # Font size
            width=120,  # Button width
            height=50,  # Button height
            corner_radius=10,  # Rounded corners
        )
        stop_button.pack()

        self.start_client()
        self.root.mainloop()


if __name__ == "__main__":
    Client().GUI()
