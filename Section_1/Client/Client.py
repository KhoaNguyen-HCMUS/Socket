import socket
import os
import customtkinter
import threading
from customtkinter import *
import math


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

        # Tạo CTkLabel để hiển thị phần trăm hoàn thành
        self.progress_label = customtkinter.CTkLabel(
            self.root, text="Download progress: 0%"
        )
        self.progress_label.pack(pady=10)

        # Tạo CTkProgressBar để hiển thị tiến trình tải xuống
        self.progress_bar = customtkinter.CTkProgressBar(self.root)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)  # Đặt giá trị ban đầu của progress bar là 0

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
        self.log_message(f"Files available:\n {'\n'.join(file_names)}")
        # self.log_message(f"Files available on server:\n {'\n'.join(processed_files)}")

    def get_new_files(self):
        with open("input.txt", "r") as f:
            current_files = f.read().splitlines()
        return [file for file in current_files if file not in self.downloaded_files]

    def request_file_download(self, file_name, count_appear):
        if file_name in self.downloaded_files:
            self.log_message(
                f"File {file_name} has already been downloaded.\n-------------"
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

                    # print(
                    #     f"\rDownload {file_name} progress: {progress_percentage:.2f}%",
                    #     end="",
                    # )

                    # Cập nhật CTkLabel để hiển thị phần trăm hoàn thành
                    self.progress_label.configure(
                        text=f"Download {file_name} progress: {progress_percentage:.2f}%"
                    )
                    self.root.update()  # Cập nhật giao diện người dùng để phản ánh sự thay đổi

                    # Cập nhật CTkProgressBar để hiển thị tiến trình tải xuống
                    self.progress_bar.set(downloaded_size / file_size)
                    self.root.update()
            # print("Download complete")
            self.log_message(f"\n Download {file_name} successful\n-------------")

        else:
            (
                self.log_message(f"File {file_name} not found on server\n-------------")
                if (count_appear[file_name] == 0)
                else None
            )

    def connect_to_server(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.client_socket.connect((self.host, self.port))
        return self.client_socket

    def run(self):
        try:
            self.client_socket = self.connect_to_server()
            self.client_socket.connect((self.host, self.port))
            if not self.client_socket.recv(1024).decode() == "accepted":
                self.log_message(
                    "Connection refused. Server is not running. Please stop client and try again later."
                )
            print("Connected to server")
            self.get_file_list()
            count_appear = {}
            while not self.client_running:
                new_files = self.get_new_files()
                list_not_exist = [
                    file for file in new_files if file not in self.file_list_from_server
                ]
                for file_name in new_files:
                    if file_name in self.downloaded_files:
                        self.log_message(f"File {file_name} already downloaded")
                    else:
                        if file_name not in count_appear:
                            count_appear[file_name] = 0
                        self.request_file_download(file_name, count_appear)
                        if file_name not in list_not_exist:
                            self.downloaded_files.add(file_name)
                        count_appear[file_name] += 1

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

    def input_file_name(self):
        file_name = self.file_input_entry.get()
        if file_name not in self.file_list_from_server:
            self.log_message(f"{file_name} is not found on Server\n-------------")
        if file_name in self.downloaded_files:
            self.log_message(f"{file_name} is already downloaded\n-------------")
        with open("input.txt", "a") as f:
            f.write("\n" + file_name)

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

        self.file_input_entry = customtkinter.CTkEntry(
            self.root, placeholder_text="Enter file name, e.g., input.txt"
        )
        self.file_input_entry.pack(pady=10)

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
