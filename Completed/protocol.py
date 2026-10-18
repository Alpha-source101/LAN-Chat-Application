import json

def encode(packet):
    return (json.dumps(packet, ensure_ascii=False) + "\n").encode("utf-8")

class Buffer:
    def __init__(self):
        self.data = b""
    def feed(self, data):
        self.data += data
        result = []
        while b"\n" in self.data:
            line, self.data = self.data.split(b"\n", 1)
            if line:
                result.append(json.loads(line.decode("utf-8")))
        return result
