import socket
import threading
from protocol import send_msg, receive_messages

HOST = "0.0.0.0"
PORT = 5000

clients = {}   # socket: username
rooms = {}     # room name: set of client sockets
lock = threading.Lock()


def send_to(client, message):
    try:
        send_msg(client, message)
        return True
    except OSError:
        return False


def broadcast(message):
    with lock:
        connected = list(clients.keys())

    for client in connected:
        send_to(client, message)


def update_users():
    with lock:
        names = list(clients.values())

    user_list = ",".join(names)
    broadcast("USERS|" + user_list)


def remove_client(client):
    with lock:
        username = clients.pop(client, None)

        for room in list(rooms.keys()):
            rooms[room].discard(client)

            if not rooms[room]:
                del rooms[room]

    try:
        client.close()
    except OSError:
        pass

    if username:
        broadcast("INFO|" + username + " left the chat")
        update_users()


def handle_client(client, address):
    buffer = ""
    username = None

    print("Connected:", address)

    try:
        while True:
            messages, buffer = receive_messages(client, buffer)

            if not messages and not buffer:
                break

            for message in messages:
                if not message:
                    continue

                parts = message.split("|", 2)
                command = parts[0]

                # Register username
                if command == "JOIN":
                    if len(parts) < 2:
                        send_to(client, "ERROR|Username required")
                        continue

                    name = parts[1].strip()

                    if not name or any(c in name for c in "\r\n|"):
                        send_to(client, "ERROR|Invalid username")
                        continue

                    with lock:
                        taken = any(
                            old_name.lower() == name.lower()
                            for old_name in clients.values()
                        )

                        if not taken and username is None:
                            username = name
                            clients[client] = username

                    if taken:
                        send_to(client, "ERROR|Username already taken")
                    elif username == name:
                        send_to(client, "INFO|Welcome " + username)
                        broadcast("INFO|" + username + " joined the chat")
                        update_users()

                # Public message
                elif command == "MSG" and username:
                    if len(parts) >= 2 and parts[1].strip():
                        broadcast("MSG|" + username + "|" + parts[1])

                # Private message: PRV|target|message
                elif command == "PRV" and username:
                    if len(parts) < 3:
                        send_to(client, "ERROR|Use PRV|username|message")
                        continue

                    target = parts[1].strip()

                    with lock:
                        target_socket = next(
                            (s for s, n in clients.items()
                             if n.lower() == target.lower()),
                            None
                        )

                    if target_socket:
                        packet = "PRV|" + username + "|" + parts[2]
                        send_to(target_socket, packet)
                        send_to(client, packet)
                    else:
                        send_to(client, "ERROR|User is offline")

                # Create or join a room
                elif command == "CREATE" and username:
                    if len(parts) < 2:
                        continue

                    room = parts[1].strip()

                    if not room or "|" in room:
                        send_to(client, "ERROR|Invalid room")
                        continue

                    with lock:
                        rooms.setdefault(room, set()).add(client)

                    send_to(client, "INFO|Joined room " + room)

                elif command == "JOINROOM" and username:
                    if len(parts) < 2:
                        continue

                    room = parts[1].strip()

                    with lock:
                        if room in rooms:
                            rooms[room].add(client)
                            joined = True
                        else:
                            joined = False

                    if joined:
                        send_to(client, "INFO|Joined room " + room)
                    else:
                        send_to(client, "ERROR|Room does not exist")

                # Leave a room
                elif command == "LEAVEROOM" and username:
                    if len(parts) < 2:
                        continue

                    room = parts[1].strip()

                    with lock:
                        if room in rooms:
                            rooms[room].discard(client)

                            if not rooms[room]:
                                del rooms[room]

                    send_to(client, "INFO|Left room " + room)

                # Room message: ROOMMSG|room|message
                elif command == "ROOMMSG" and username:
                    if len(parts) < 3:
                        continue

                    room = parts[1].strip()

                    with lock:
                        members = list(rooms.get(room, set()))

                    if client not in members:
                        send_to(client, "ERROR|Join room first")
                        continue

                    packet = "ROOMMSG|" + room + "|" + username + "|" + parts[2]

                    for member in members:
                        send_to(member, packet)

                elif command == "USERS" and username:
                    with lock:
                        names = ",".join(clients.values())

                    send_to(client, "USERS|" + names)

                elif command == "QUIT":
                    return

                elif not username:
                    send_to(client, "ERROR|Send JOIN first")

    except (OSError, UnicodeDecodeError):
        pass

    finally:
        remove_client(client)
        print("Disconnected:", address)


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server.bind((HOST, PORT))
        server.listen(10)

        print("Server started on port", PORT)
        print("Press Ctrl+C to stop")

        while True:
            client, address = server.accept()

            threading.Thread(
                target=handle_client,
                args=(client, address),
                daemon=True
            ).start()

    except KeyboardInterrupt:
        print("\nServer stopped")

    except OSError as error:
        print("Server error:", error)

    finally:
        server.close()


if __name__ == "__main__":
    main()