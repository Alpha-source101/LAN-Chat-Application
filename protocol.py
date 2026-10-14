import socket

def send_msg(client, message):
    client.sendall((message + "\n").encode())

def receive_messages(client, buffer):
    data = client.recv(4096)

    if not data:
        return [], ""

    buffer += data.decode()

    messages = buffer.split("\n")

    return messages[:-1], messages[-1]