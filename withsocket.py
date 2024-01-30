import tkinter as tk
from tkinter import ttk
from threading import Thread, Event
import socket
import time

class Sender:
    def __init__(self, window_size, timeout, gui, host, port):
        self.window_size = window_size
        self.timeout = timeout
        self.gui = gui
        self.frames = ""
        self.receiver_address = (host, port)
        self.counter = 1
        self.is_running = False
        self.event = Event()

    def start(self, frames):
        self.frames = frames
        self.is_running = True
        self.send_frame()

    def send_frame(self):
        if not self.is_running:
            return

        frame_start = (self.counter - 1) * self.window_size
        frame_end = min(len(self.frames), self.counter * self.window_size)
        frames_to_send = self.frames[frame_start:frame_end]

        self.gui.update_sender_message(f"Sending frames {frame_start} to {frame_end}")

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sender_socket:
                sender_socket.connect(self.receiver_address)
                sender_socket.sendall(frames_to_send.encode())

                response = sender_socket.recv(1024).decode()
                self.gui.update_sender_message(response)

                if response == "RR":
                    old_counter = self.counter
                    self.counter += 1

                    if old_counter * self.window_size > len(self.frames):
                        self.gui.update_sender_message("Successful")
                        self.is_running = False
                elif response == "REJ":
                    # If rejected, resend the same frame
                    self.gui.update_sender_message("Resending frames due to rejection")
                    self.counter = old_counter
        except Exception as e:
            self.gui.update_sender_message(f"Error: {e}")

        # Schedule the next frame regardless of the thread state
        self.gui.root.after(1000, self.send_frame)

class Receiver:
    def __init__(self, window_size, host, port):
        self.window_size = window_size
        self.count = 1
        self.time_out_test_passed = False
        self.reject_test_passed = False
        self.message = ""
        self.receiver_address = (host, port)

    def receive(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as receiver_socket:
                print(f"Receiver is binding to {self.receiver_address}")
                receiver_socket.bind(self.receiver_address)
                print("Receiver is listening...")
                receiver_socket.listen()

                try:
                    conn, addr = receiver_socket.accept()
                    print(f"Receiver accepted connection from {addr}")
                except Exception as e:
                    print(f"Error accepting connection: {e}")
                    return  # Exit the method if there is an error accepting the connection

                with conn:
                    while True:
                        data = conn.recv(1024).decode()

                        if not data:
                            break

                        if self.count == 4 and not self.time_out_test_passed:
                            self.time_out_test_passed = True
                            time.sleep(5)
                            conn.sendall("RR".encode())
                            break
                        elif self.count == 6 and not self.reject_test_passed:
                            self.reject_test_passed = True
                            time.sleep(1)
                            conn.sendall("REJ".encode())
                            break

                        time.sleep(1)

                        if len(data) != self.window_size:
                            conn.sendall("REJ".encode())
                            break

                        self.message += data
                        conn.sendall("RR".encode())
                        self.count += 1

        except Exception as e:
            print(f"Error in Receiver: {e}")

        return self.message
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Go-Back-N Protocol Simulator")
        self.receiver_thread = None
        self.sender = None
        self.sender_message_text = tk.StringVar()
        self.receiver_message_text = tk.StringVar()
        self.message_to_send = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self.root, text="Enter the window size:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        self.window_size_entry = ttk.Entry(self.root)
        self.window_size_entry.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(self.root, text="Enter the timeout in seconds:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        self.timeout_entry = ttk.Entry(self.root)
        self.timeout_entry.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(self.root, text="Enter the message to send:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        self.message_to_send_entry = ttk.Entry(self.root, textvariable=self.message_to_send)
        self.message_to_send_entry.grid(row=2, column=1, padx=10, pady=5)
        self.message_to_send.set("This message is just for test and must be a long sentence.")

        self.sender_button = ttk.Button(self.root, text="Start Sender", command=self.start_sender)
        self.sender_button.grid(row=3, column=0, columnspan=2, pady=10)

        self.sender_message_label = ttk.Label(self.root, text="Sender Messages:")
        self.sender_message_label.grid(row=4, column=0, columnspan=2, pady=5)

        self.sender_message_display = tk.Text(self.root, height=8, width=50, state="normal")
        self.sender_message_display.config(state="disabled")
        self.sender_message_display.grid(row=5, column=0, columnspan=2, pady=5)

        self.sender_message_scrollbar = ttk.Scrollbar(self.root, command=self.sender_message_display.yview)
        self.sender_message_scrollbar.grid(row=5, column=2, sticky="ns")
        self.sender_message_display.config(yscrollcommand=self.sender_message_scrollbar.set)

        ttk.Label(self.root, text="Receiver Messages:").grid(row=6, column=0, columnspan=2, pady=5)
        self.receiver_message_display = tk.Text(self.root, height=8, width=50, state="normal")
        self.receiver_message_display.config(state="disabled")
        self.receiver_message_display.grid(row=7, column=0, columnspan=2, pady=5)

        self.receiver_message_scrollbar = ttk.Scrollbar(self.root, command=self.receiver_message_display.yview)
        self.receiver_message_scrollbar.grid(row=7, column=2, sticky="ns")
        self.receiver_message_display.config(yscrollcommand=self.receiver_message_scrollbar.set)

    def start_receiver(self):
        window_size = int(self.window_size_entry.get())
        self.receiver = Receiver(window_size, '127.0.0.1', 8080)
        self.clear_sender_message()
        self.clear_receiver_message()

        self.receiver_thread = Thread(target=self.receiver.receive)
        self.receiver_thread.start()

    def start_sender(self):
        window_size = int(self.window_size_entry.get())
        timeout = int(self.timeout_entry.get())
        message_to_send = self.message_to_send.get()

        self.sender = Sender(window_size, timeout, self, '127.0.0.1', 8080)
        self.clear_sender_message()
        self.clear_receiver_message()

        Thread(target=self.sender.start, args=(message_to_send,)).start()

    def update_sender_message(self, message):
        self.sender_message_display.config(state="normal")
        self.sender_message_display.insert(tk.END, message + "\n")
        self.sender_message_display.config(state="disabled")

    def clear_sender_message(self):
        self.sender_message_display.config(state="normal")
        self.sender_message_display.delete(1.0, tk.END)
        self.sender_message_display.config(state="disabled")

    def update_receiver_message(self, message):
        self.receiver_message_display.config(state="normal")
        self.receiver_message_display.insert(tk.END, message + "\n")
        self.receiver_message_display.config(state="disabled")

    def clear_receiver_message(self):
        self.receiver_message_display.config(state="normal")
        self.receiver_message_display.delete(1.0, tk.END)
        self.receiver_message_display.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
