import time
from threading import Thread


class Sender:
    def __init__(self, window_size, timeout):
        self.window_size = window_size
        self.timeout = timeout

    def send(self, frames, reciver):
        counter = 1
        while True:
            frame_start = (counter - 1) * self.window_size
            frame_end = min(len(frames), counter * self.window_size)

            frames_to_send = frames[frame_start:frame_end]

            print(f"Sending frames {frame_start} to {frame_end}")

            response = []
            thread = Thread(
                target=reciver.recive,
                args=(
                    frames_to_send,
                    counter * self.window_size > len(frames),
                    response,
                ),
            )
            thread.start()
            thread.join(self.timeout)
            if thread.is_alive():
                print("Timeout")
                continue

            result = response.pop()
            print(f"{result}{counter}" if result == "RR" else f"{result}")

            old_counter = counter
            if result == "RR":
                counter += 1
            elif result == "REJ":
                continue

            if old_counter * self.window_size > len(frames):
                break

        print("Successful")


class Reciver:
    def __init__(self, window_size):
        self.window_size = window_size
        self.count = 1
        self.time_out_test_passed = False
        self.reject_test_passed = False
        self.message = ""

    def recive(self, frames, is_last_window, result):
        if self.count == 4 and not self.time_out_test_passed:
            self.time_out_test_passed = True
            time.sleep(5)
            return
        elif self.count == 6 and not self.reject_test_passed:
            self.reject_test_passed = True
            time.sleep(1)
            result.append("REJ")
            return

        time.sleep(1)

        if len(frames) != window_size and not is_last_window:
            result.append("REJ")
            return

        self.message += frames
        result.append("RR")
        self.count += 1


window_size = int(input("Enter the window size: "))
sender = Sender(window_size, int(input("Enter the timeout in seconds: ")))
reciver = Reciver(window_size)
frames = "Hello, this is a test message for Go-Back-N protocol."
sender.send(frames, reciver)
print(reciver.message)
