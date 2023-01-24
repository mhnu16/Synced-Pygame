import json
import socket

LENGTH_HEADER = 8


def send_message(client_socket: socket.socket, json_data: str):
    """
    Adds to the data the required LENGTH_HEADER and sends it to the client.

    ---
    :param client_socket: the socket to send the data to
    :param json_data: the data to send to the client (formatted as JSON string)

    ---
    :return: None
    """
    # Encode the data into bytes
    data = json_data.encode()

    # Get the length of the data and convert it to bytes
    data_length = len(data)

    # Add the length header to the data
    data = f"{str(data_length).zfill(LENGTH_HEADER)}".encode() + data

    # Send the data to the client
    client_socket.send(data)


def receive_message(client_socket: socket.socket) -> str:
    """
    Reads the length header and receives that amount of bytes from the client.

    ---
    :param client_socket: the socket that receives the data

    ---
    :return: The data received from the client
    """
    try:
        # Receive the length header from the client
        data_length_bytes = client_socket.recv(LENGTH_HEADER)

    except ConnectionResetError:
        # If the client has disconnected, return a QUIT message
        return json.dumps(["QUIT"])

    try:
        data_length = int(data_length_bytes)

        data = client_socket.recv(data_length)

        data = data.decode()

        return data

    except ValueError:
        # If the length header is not an integer, the client has disconnected
        return json.dumps(["QUIT"])
