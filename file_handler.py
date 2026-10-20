import os

CHUNK_SIZE = 4096
FILE_PORT = 5001
MAX_FILE_SIZE = 100 * 1024 * 1024

def get_file_info(path):
    return os.path.basename(path), os.path.getsize(path)

def read_file(path):
    with open(path, "rb") as f:
        return f.read()

def read_file_chunks(path, chunk_size=CHUNK_SIZE):
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk

def send_file(path, sock):
    for chunk in read_file_chunks(path):
        sock.sendall(chunk)

def safe_filename(name):
    return os.path.basename(name).replace("\x00", "") or "received_file"

def receive_exact(sock, size, path):
    remaining = size
    with open(path, "wb") as f:
        while remaining:
            chunk = sock.recv(min(CHUNK_SIZE, remaining))
            if not chunk:
                raise ConnectionError("Connection ended before file was complete")
            f.write(chunk)
            remaining -= len(chunk)
