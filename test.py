import socket
import threading

def handle_client(client_socket, client_address):
    # Handle individual client connection
    print(f"Connection from {client_address}")

    # Receive data from the client
    data = client_socket.recv(1024)
    print(f"Received data: {data.decode('utf-8')}")

    # Send a response back to the client
    response = "Hello, client! This is the server."
    client_socket.send(response.encode('utf-8'))

    # Close the connection
    client_socket.close()

def client_logic():
    # Client (sender) part
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 8080))

    # Send data to the server
    message = "Hello, server! This is the client."
    client_socket.send(message.encode('utf-8'))

    # Receive the response from the server
    response = client_socket.recv(1024)
    print(f"Received response: {response.decode('utf-8')}")

    # Close the connection
    client_socket.close()

def main():
    # Define the host and port
    host = '127.0.0.1'
    port = 8080

    # Create a socket object
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to a specific address and port
    server_socket.bind((host, port))

    # Listen for incoming connections
    server_socket.listen(5)
    print(f"Server listening on {host}:{port}")

    while True:
        # Accept a connection from a client
        client_socket, client_address = server_socket.accept()

        # Create a new thread for each client connection
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()

        # Run client logic in a separate thread
        client_logic_thread = threading.Thread(target=client_logic)
        client_logic_thread.start()

if __name__ == "__main__":
    main()
