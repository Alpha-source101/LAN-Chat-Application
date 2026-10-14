import socket
import threading

from protocol import send_msg, receive_messages

HOST = "127.0.0.1"
PORT = 5000

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

buffer = ""


def receive():
    global buffer

    while True:
        try:
            messages, buffer = receive_messages(client, buffer)

            if not messages and not buffer:
                break

            for message in messages:
                print("\n" + message)

        except (OSError, UnicodeDecodeError):
            break


threading.Thread(target=receive, daemon=True).start()

username = input("Enter username: ")
send_msg(client, "JOIN|" + username)

print("Type a message, or /quit to exit")

try:
    while True:
        message = input("> ")

        if message == "/quit":
            send_msg(client, "QUIT")
            break

        send_msg(client, "MSG|" + message)

except (KeyboardInterrupt, EOFError):
    pass

finally:
    client.close()