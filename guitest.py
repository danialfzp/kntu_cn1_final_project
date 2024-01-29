import tkinter as tk
from tkinter import ttk
from threading import Thread, Event
import time

class Sender:
    def __init__(self, window_size, timeout, gui):
        self.window_size = window_size
        self.timeout = timeout
        self.gui = gui
        self.frames = ""
        self.receiver = None
        self.counter = 1
        self.is_running = False
        self.event = Event()

    def start(self, frames, receiver):
        self.frames = frames
        self.receiver = receiver
        self.is_running = True
        self.send_frame()

    def send_frame(self):
        if not self.is_running:
            return

        frame_start = (self.counter - 1) * self.window_size
        frame_end = min(len(self.frames), self.counter * self.window_size)
        frames_to_send = self.frames[frame_start:frame_end]

        self.gui.update_sender_message(f"Sending frames {frame_start} to {frame_end}")

        response = []
        thread = Thread(
            target=self.receiver.receive,
            args=(
                frames_to_send,
                self.counter * self.window_size > len(self.frames),
                response,
                self.event,  # Pass the event to the receiver thread
            ),
        )
        thread.response = response  # Store response as an attribute of the thread
        thread.start()

        # Use after to check if the thread has completed after the timeout
        self.gui.root.after(self.timeout * 1000, self.check_thread_status, thread)

    def check_thread_status(self, thread):
        if thread.is_alive():
            self.gui.update_sender_message("Timeout")
            thread.join()  # Wait for the thread to complete
        else:
            response = thread.response  # Access the response directly
            result = response.pop() if response else None
            self.gui.update_sender_message("Thread completed successfully")

            if result:
                self.gui.update_sender_message(f"{result}{self.counter}" if result == "RR" else f"{result}")

                old_counter = self.counter
                if result == "RR":
                    self.counter += 1
                elif result == "REJ":
                    # If rejected, resend the same frame
                    self.counter = old_counter

                if old_counter * self.window_size > len(self.frames):
                    self.gui.update_sender_message("Successful")
                    self.is_running = False

        # Schedule the next frame regardless of the thread state
        self.gui.root.after(1000, self.send_frame)

class Receiver:
    def __init__(self, window_size):
        self.window_size = window_size
        self.count = 1
        self.time_out_test_passed = False
        self.reject_test_passed = False
        self.message = ""

    def receive(self, frames, is_last_window, result, event):
        if self.count == 4 and not self.time_out_test_passed:
            self.time_out_test_passed = True
            time.sleep(5)
            event.set()  # Signal the main thread that the task is done
            return
        elif self.count == 6 and not self.reject_test_passed:
            self.reject_test_passed = True
            time.sleep(1)
            result.append("REJ")
            event.set()  # Signal the main thread that the task is done
            return

        time.sleep(1)

        if len(frames) != self.window_size and not is_last_window:
            result.append("REJ")
            event.set()  # Signal the main thread that the task is done
            return

        self.message += frames
        result.append("RR")
        self.count += 1
        event.set()  # Signal the main thread that the task is done

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Go-Back-N Protocol Simulator")

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

        ttk.Label(self.root, text="Enter message to send:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        self.message_entry = ttk.Entry(self.root, textvariable=self.message_to_send)
        self.message_entry.grid(row=2, column=1, padx=10, pady=5)

        self.sender_button = ttk.Button(self.root, text="Start Sender", command=self.start_sender)
        self.sender_button.grid(row=3, column=0, columnspan=2, pady=10)

        # Scrollbar for Sender Messages
        self.sender_scrollbar = tk.Scrollbar(self.root)
        self.sender_scrollbar.grid(row=5, column=2, sticky=tk.NS)
        
        self.sender_message_label = ttk.Label(self.root, text="Sender Messages:")
        self.sender_message_label.grid(row=4, column=0, columnspan=2, pady=5)

        self.sender_message_display = tk.Text(self.root, height=8, width=50, state="disabled", yscrollcommand=self.sender_scrollbar.set)
        self.sender_message_display.grid(row=5, column=0, columnspan=2, pady=5)
        self.sender_scrollbar.config(command=self.sender_message_display.yview)

        # Scrollbar for Receiver Messages
        self.receiver_scrollbar = tk.Scrollbar(self.root)
        self.receiver_scrollbar.grid(row=7, column=2, sticky=tk.NS)

        self.receiver_message_label = ttk.Label(self.root, text="Receiver Messages:")
        self.receiver_message_label.grid(row=6, column=0, columnspan=2, pady=5)

        self.receiver_message_display = tk.Text(self.root, height=8, width=50, state="disabled", yscrollcommand=self.receiver_scrollbar.set)
        self.receiver_message_display.grid(row=7, column=0, columnspan=2, pady=5)
        self.receiver_scrollbar.config(command=self.receiver_message_display.yview)

    def start_sender(self):
        window_size = int(self.window_size_entry.get())
        timeout = int(self.timeout_entry.get())
        message_to_send = self.message_to_send.get()

        sender = Sender(window_size, timeout, self)
        receiver = Receiver(window_size)

        self.clear_sender_message()
        self.clear_receiver_message()

        sender.start(message_to_send, receiver)

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
