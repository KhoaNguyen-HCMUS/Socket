import os
import socket
import threading
from time import sleep
import customtkinter
from customtkinter import *

SEPARATOR = " "
FORMAT = "utf-8"
PRIOR_MAP = {"CRITICAL": 10, "HIGH": 4, "NORMAL": 1}
LINEBREAK = "----------------------------------------\n"


class Client:
    def __init__(self):
        self.host = "127.0.0.1"
        self.port = 65432
        self.client_socket = None
        self.file_list = {}
        self.download_queue = {}
        self.download_status = {}
        self.files_not_found = []
        self.signal = threading.Event()

        self.root = customtkinter.CTk()
        self.progress_bars = {}
        self.labels = {}
        self.percent_labels = {}
        self.next_y = 10
        self.text_widget = None

    def get_file_list(self):
        self.client_socket.sendall("LIST".encode(FORMAT))
        lst = self.client_socket.recv(1024).decode(FORMAT)
        lst = lst.strip().split("\n")
        lst = [file.split(SEPARATOR) for file in lst]

        self.log_message("File list:")
        for file_name, file_size in lst:
            self.file_list[file_name] = int(file_size)
            self.log_message(file_name + " - " + self.get_standard_size(int(file_size)))

    def read_input_files(self):
        while not self.signal.is_set():
            with open("input.txt", "r") as f:
                input_files = f.read().strip().split("\n")
                input_files = [file.split(SEPARATOR) for file in input_files]

                for file in input_files:
                    if file[0] not in self.file_list:
                        if file[0] in self.files_not_found:
                            continue
                        self.log_message(f"{LINEBREAK}File {file[0]} not found.")
                        self.files_not_found.append(file[0])
                        continue

                    priority_size = 1024
                    if len(file) > 1:
                        priority_size = self.get_priority_size(file[1])
                    if file[0] not in self.download_status:
                        self.download_status[file[0]] = [priority_size, False]
                        self.download_queue[file[0]] = priority_size
                        with open(os.path.join("Output", file[0]), "wb") as f:
                            pass
                        self.create_progress_bar(file[0])
            sleep(2)

    def get_standard_size(self, size):
        itme = ["B", "KB", "MB", "GB", "TB"]
        for x in itme:
            if size < 1024.0:
                return "%3.1f%s" % (size, x)
            size /= 1024.0
        return size

    def get_priority_size(self, file_priority):
        return 1024 * PRIOR_MAP.get(file_priority, 1)

    def write_file(self, file_name, data):
        with open(os.path.join("Output", file_name), "ab") as f:
            f.write(data)

    def is_all_done(self, status):
        return all([status[1] for status in status.values()])

    def client_request(self):
        while not self.signal.is_set():
            self.client_socket.sendall("get".encode(FORMAT))
            download_status_copy = self.download_status.copy()

            try:
                while not self.signal.is_set():
                    download_queue_copy = self.download_queue.copy()
                    eliminate_files = []

                    if self.is_all_done(download_status_copy):
                        break

                    for file_name, priority_size in download_queue_copy.items():
                        # if file_name in self.download_status:
                        #     if self.download_status[file_name][1]:
                        #         self.log_message(f"File {file_name} already downloaded.")
                        #         continue

                        self.client_socket.sendall(
                            f"GET{SEPARATOR}{file_name}{SEPARATOR}{priority_size}".encode(
                                FORMAT
                            )
                        )
                        response = self.client_socket.recv(priority_size)

                        if response == b"EOF" or len(response) == 0 or not response:
                            eliminate_files.append(file_name)
                            self.download_status[file_name][1] = True
                        else:
                            if len(self.download_status[file_name]) < 3:
                                self.download_status[file_name].append(0)

                            # self.download_status[file_name][2] += len(response)
                            self.write_file(file_name, response)

                            current_size = os.path.getsize(
                                os.path.join("Output", file_name)
                            )

                            self.update_progress_bar(
                                file_name, current_size / self.file_list[file_name]
                            )
                            if current_size >= self.file_list[file_name]:
                                self.download_status[file_name][1] = True
                                self.log_message(
                                    f"{LINEBREAK}Downloaded file {file_name} successfully."
                                )
                                eliminate_files.append(file_name)

                    download_queue_copy.clear()
                    for file_name in eliminate_files:
                        if file_name in self.download_queue:
                            del self.download_queue[file_name]

                download_status_copy.clear()
                self.client_socket.sendall("done".encode(FORMAT))
            except Exception:
                self.signal.set()
                self.log_message(
                    "Error: Server interrupted, connection was forcibly closed by the remote host."
                )
                self.client_socket.close()
                break

    def start_client(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))

            self.get_file_list()

            thread = threading.Thread(target=self.read_input_files)
            thread.start()

            sleep(0.25)
            self.client_request()
        except KeyboardInterrupt:
            self.signal.set()
            self.client_socket.sendall("terminate".encode(FORMAT))
            self.log_message("\nClient is closing...")
            self.log_message("Client closed.")
        except ConnectionRefusedError:
            self.log_message("Connection refused. Server not responding.")
            self.log_message("Client closed.")
        except Exception as e:
            self.log_message(
                "Error: Server interrupted, connection was forcibly closed by the remote host."
            )
        finally:
            self.signal.set()
            self.client_socket.close()

    def stop_client(self):
        try:
            self.log_message("Stopping client...")
            self.signal.set()
            if self.client_socket:
                self.client_socket.sendall("terminate".encode(FORMAT))
                self.client_socket.close()
                self.root.quit()
        except Exception as e:
            self.log_message(f"An error occurred while stopping the client: {e}")
        finally:
            self.root.quit()  # Ensure the GUI window is closed

    def log_message(self, message):
        if self.text_widget:
            self.text_widget.insert(customtkinter.END, message + "\n")
            self.text_widget.see(customtkinter.END)
        print(message)

    def create_progress_bar(self, name):
        label = customtkinter.CTkLabel(self.progress_frame, text=name)
        label.place(x=10, y=self.next_y)
        progress_bar = customtkinter.CTkProgressBar(self.progress_frame, width=200)
        progress_bar.place(x=10, y=self.next_y + 20)
        percent_label = customtkinter.CTkLabel(self.progress_frame, text="0%")
        percent_label.place(x=220, y=self.next_y + 20)
        self.progress_bars[name] = progress_bar
        self.labels[name] = label
        self.percent_labels[name] = percent_label
        self.next_y += 50

    def update_progress_bar(self, name, value):
        if name in self.progress_bars:
            self.progress_bars[name].set(value)
            self.percent_labels[name].configure(text=f"{int(value * 100)}%")
        else:
            pass

    def add_placeholder(self, event):
        if not self.file_input_textbox.get("1.0", "end-1c"):
            self.file_input_textbox.insert(
                "1.0", "Enter file name and priority, e.g., input.txt NORMAL"
            )

    def clear_placeholder(self, event):
        if (
            self.file_input_textbox.get("1.0", "end-1c")
            == "Enter file name and priority, e.g., input.txt NORMAL"
        ):
            self.file_input_textbox.delete("1.0", "end")

    def input_file_name(self):
        file_name = self.file_input_textbox.get("1.0", "end-1c").strip()
        with open("input.txt", "a") as f:
            f.write("\n" + file_name)

    def GUI(self):
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
        header.grid(row=0, column=0, columnspan=2, pady=10)

        # Create frames
        self.text_frame = customtkinter.CTkScrollableFrame(
            self.root, width=300, height=300
        )
        self.text_frame.grid(row=1, column=0, sticky="nsew")

        self.progress_frame = customtkinter.CTkFrame(self.root, width=300, height=400)
        self.progress_frame.grid(row=1, column=1, sticky="nsew")

        # Add text box to text_frame
        self.text_box = customtkinter.CTkTextbox(
            self.text_frame, width=280, height=400, fg_color="white", text_color="black"
        )
        self.text_box.grid(padx=10, pady=10)
        self.text_widget = self.text_box

        # Create a new frame for the exit button
        self.exit_frame = customtkinter.CTkFrame(
            self.root, width=600, height=100, fg_color="lightgray"
        )
        self.exit_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")

        # Add file input entry
        self.file_input_textbox = customtkinter.CTkTextbox(
            self.exit_frame,
            width=200,
            height=100,
            fg_color="white",
            text_color="black",
        )
        self.file_input_textbox.insert(
            "1.0", "Enter file name and priority, e.g., input.txt NORMAL"
        )
        self.file_input_textbox.bind("<FocusIn>", self.clear_placeholder)
        self.file_input_textbox.bind("<FocusOut>", self.add_placeholder)
        self.file_input_textbox.grid(row=0, column=1, pady=10, padx=10, sticky="ew")

        # Add enter button
        self.enter_button = customtkinter.CTkButton(
            self.exit_frame,
            text="Enter",
            command=self.input_file_name,
            fg_color="#007BFF",  # Button color
            text_color="white",  # Text color
            font=("Arial", 16),
        )
        self.enter_button.grid(row=0, column=2, pady=10, padx=10, sticky="ew")

        # Add stop client button
        self.stop_button = customtkinter.CTkButton(
            self.exit_frame,
            text="Stop Client",
            command=self.stop_client,
            fg_color="#FF6F61",
            text_color="white",
            width=120,  # Button width
            height=50,  # Button height
            corner_radius=10,
        )
        self.stop_button.grid(
            row=1, column=1, pady=20, padx=10, sticky="ew", columnspan=2
        )

        # Configure grid weights to ensure proper resizing
        self.exit_frame.grid_columnconfigure(0, weight=1)
        self.exit_frame.grid_columnconfigure(1, weight=1)
        self.exit_frame.grid_columnconfigure(2, weight=1)
        self.exit_frame.grid_columnconfigure(3, weight=1)

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        threading.Thread(target=self.start_client, daemon=True).start()
        # self.start_client()
        self.root.mainloop()


if __name__ == "__main__":
    client = Client()
    client.GUI()
