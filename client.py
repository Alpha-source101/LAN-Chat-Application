import json, os, socket, threading
from protocol import encode, Buffer
from file_handler import FILE_PORT, send_file, receive_exact, safe_filename

class ChatClient:
    def __init__(self, host, port=5000, callback=None):
        self.host, self.port = host, port
        self.callback = callback or (lambda event: None)
        self.sock = None; self.username = ""; self.connected = False
        self.lock = threading.Lock()

    def connect(self, username):
        self.username = username.strip()
        self.sock = socket.create_connection((self.host,self.port),timeout=8)
        self.sock.settimeout(None); self.connected=True
        threading.Thread(target=self._receive,daemon=True).start()
        self.send({"type":"JOIN","username":self.username})

    def send(self, packet):
        if not self.connected or not self.sock: return
        try:
            with self.lock: self.sock.sendall(encode(packet))
        except OSError as exc: self.callback({"type":"ERROR","text":str(exc)})

    def _receive(self):
        buf=Buffer()
        try:
            while self.connected:
                data=self.sock.recv(4096)
                if not data: break
                for event in buf.feed(data): self.callback(event)
        except (OSError,ValueError,json.JSONDecodeError) as exc:
            if self.connected: self.callback({"type":"ERROR","text":str(exc)})
        finally:
            self.connected=False; self.callback({"type":"DISCONNECTED"})

    def public(self,text): self.send({"type":"MSG","text":text})
    def private(self,target,text): self.send({"type":"PRV","target":target,"text":text})
    def create_room(self,room): self.send({"type":"CREATE","room":room})
    def join_room(self,room): self.send({"type":"JOINROOM","room":room})
    def leave_room(self): self.send({"type":"LEAVEROOM"})
    def offer_file(self,target,path):
        self.pending_path=path
        self.send({"type":"FILE_OFFER","target":target,"filename":os.path.basename(path),"size":os.path.getsize(path)})

    @staticmethod
    def _read_header(sock):
        data=b""
        while b"\n" not in data:
            chunk=sock.recv(1)
            if not chunk: raise ConnectionError("Server closed transfer")
            data+=chunk
            if len(data)>8192: raise ValueError("Invalid transfer header")
        return json.loads(data[:-1].decode())

    def upload(self,tid,size,path):
        try:
            with socket.create_connection((self.host,FILE_PORT),timeout=10) as s:
                s.sendall((json.dumps({"action":"UPLOAD","transfer_id":tid,"sender":self.username,"size":size})+"\n").encode())
                response=self._read_header(s)
                if not response.get("ok"): raise RuntimeError(response.get("error","Upload refused"))
                send_file(path,s)
        except (OSError,ValueError,RuntimeError) as exc: self.callback({"type":"ERROR","text":f"Upload failed: {exc}"})

    def download(self,tid):
        try:
            os.makedirs("received_files",exist_ok=True)
            with socket.create_connection((self.host,FILE_PORT),timeout=10) as s:
                s.sendall((json.dumps({"action":"DOWNLOAD","transfer_id":tid,"username":self.username})+"\n").encode())
                header=self._read_header(s)
                if not header.get("ok"): raise RuntimeError(header.get("error","Download refused"))
                name=safe_filename(header["filename"]); path=os.path.join("received_files",name)
                root,ext=os.path.splitext(path); n=1
                while os.path.exists(path): path=f"{root}_{n}{ext}"; n+=1
                receive_exact(s,int(header["size"]),path)
            self.callback({"type":"FILE_RECEIVED","filename":os.path.basename(path),"path":path})
        except (OSError,ValueError,RuntimeError,KeyError) as exc: self.callback({"type":"ERROR","text":f"Download failed: {exc}"})

    def call(self,target,mode): self.send({"type":"CALL_REQUEST","target":target,"mode":mode})
    def respond(self,cid,accepted): self.send({"type":"CALL_RESPONSE","call_id":cid,"accepted":accepted})
    def end_call(self,cid): self.send({"type":"CALL_END","call_id":cid})

    def close(self):
        if self.connected: self.send({"type":"QUIT"})
        self.connected=False
        try: self.sock.shutdown(socket.SHUT_RDWR)
        except (OSError,AttributeError): pass
        try: self.sock.close()
        except (OSError,AttributeError): pass
