import tkinter as tk
from tkinter import ttk
import threading
import time

def simulate_download(progress_bar, label):
    for i in range(101):
        progress_bar['value'] = i
        label.config(text=f"Download progress: {i}%")
        window.update_idletasks()
        time.sleep(0.1)  # Simulate time between downloads

def start_download():
    threading.Thread(target=simulate_download, args=(progress_bar, label)).start()

def handle_ctrl_c(event):
    print("Ctrl + C detected. Exiting...")
    window.destroy()

window = tk.Tk()
window.title("Client-Server File Download")
window.geometry("400x200")

label = tk.Label(window, text="Click 'Start Download' to begin")
label.pack(pady=10)

progress_bar = ttk.Progressbar(window, orient="horizontal", length=300, mode="determinate")
progress_bar.pack(pady=10)

start_button = tk.Button(window, text="Start Download", command=start_download)
start_button.pack(pady=10)

# Bind Ctrl + C event to the handler function
window.bind("<Control-c>", handle_ctrl_c)

window.mainloop()