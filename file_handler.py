import os


def get_file_info(file_path):
    filename = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)

    return filename, file_size

def read_file(file_path):
    with open(file_path, "rb") as file:
        data = file.read()
    return data

def save_file(filename, data):
    os.makedirs("received_files", exist_ok=True)
    file_path = os.path.join("received_files", filename)
    with open(file_path, "wb") as file:
        file.write(data)
    return file_path


def read_file_chunks(file_path, chunk_size=4096):
    with open(file_path, "rb") as file:
        while True:
            chunk = file.read(chunk_size)

            if not chunk:
                break

            yield chunk


def send_file(file_path, sock):
    with open(file_path, "rb") as file:
        while True:
            chunk = file.read(4096)

            if not chunk:
                break

            sock.sendall(chunk)