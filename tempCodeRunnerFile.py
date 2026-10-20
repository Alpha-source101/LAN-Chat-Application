import json, os, socket, threading, uuid
from protocol import encode, Buffer
from file_handler import FILE_PORT, MAX_FILE_SIZE, safe_filename, receive_exact

HOST, CHAT_PORT = "0.0.0.0", 5000
SAVE_DIR = "server_received"
clients = {}       # socket -> {"name": str, "room": str}
rooms = {"General": set()}
files = {}         # transfer id -> metadata
calls = {}
lock = threading.RLock()

def send(sock, packet):
    try:
        sock.sendall(encode(packet))
        return True
    except OSError:
        return False

def broadcast(packet, recipients=None):
    with lock:
        targets = list(clients if recipients is None else recipients)
    for target in targets:
        send(target, packet)

def user_socket(name):
    with lock:
        return next((s for s, v in clients.items() if v["name"].casefold() == name.casefold()), None)

def presence():
    with lock:
        users = sorted(v["name"] for v in clients.values())
        room_names = sorted(rooms)
    broadcast({"type":"USERS", "users":users})
    broadcast({"type":"ROOMS", "rooms":room_names})

def remove(sock):
    with lock:
        info = clients.pop(sock, None)
        if not info:
            return
        for room in list(rooms):
            rooms[room].discard(sock)
            if room != "General" and not rooms[room]:
                del rooms[room]
        name = info["name"]
    try: sock.close()
    except OSError: pass
    broadcast({"type":"INFO", "text":f"{name} left the chat"})
    presence()

def handle_client(sock, addr):
    buffer, name = Buffer(), None
    print("[CHAT CONNECTED]", addr)
    try:
        running = True
        while running:
            data = sock.recv(4096)
            if not data: break
            for p in buffer.feed(data):
                cmd = p.get("type")
                with lock:
                    info = clients.get(sock)
                    name = info["name"] if info else None
                if cmd == "JOIN":
                    new_name = str(p.get("username","")).strip()
                    with lock:
                        taken = any(v["name"].casefold() == new_name.casefold() for v in clients.values())
                        if new_name and len(new_name) <= 24 and not taken and sock not in clients:
                            clients[sock] = {"name":new_name, "room":"General"}
                            rooms["General"].add(sock)
                            ok = True
                        else: ok = False
                    if ok:
                        name = new_name
                        send(sock, {"type":"JOINED","username":name})
                        broadcast({"type":"INFO","text":f"{name} joined the chat"})
                        presence()
                    else:
                        send(sock, {"type":"ERROR","text":"Invalid or already-used username (1-24 characters)."})
                elif not name:
                    send(sock, {"type":"ERROR","text":"Join the chat first."})
                elif cmd == "MSG":
                    text = str(p.get("text","")).strip()
                    if text:
                        with lock:
                            room = clients[sock]["room"]
                            members = list(rooms[room])
                        broadcast({"type":"ROOMMSG","room":room,"sender":name,"text":text}, members)
                elif cmd == "PRV":
                    target, text = str(p.get("target","")).strip(), str(p.get("text","")).strip()
                    peer = user_socket(target)
                    if peer and text:
                        item = {"type":"PRV","sender":name,"target":target,"text":text}
                        send(peer,item); send(sock,item)
                    else: send(sock, {"type":"ERROR","text":"User is offline or message is empty."})
                elif cmd == "CREATE":
                    room = str(p.get("room","")).strip()
                    if not room or len(room)>32:
                        send(sock, {"type":"ERROR","text":"Room name must be 1-32 characters."}); continue
                    with lock:
                        exists = room in rooms
                        if not exists: rooms[room] = set()
                    send(sock, {"type":"ERROR" if exists else "INFO","text":"Room already exists." if exists else f"Room '{room}' created."})
                    presence()
                elif cmd == "JOINROOM":
                    room = str(p.get("room","")).strip()
                    with lock:
                        if room in rooms:
                            old = clients[sock]["room"]
                            rooms[old].discard(sock); rooms[room].add(sock)
                            clients[sock]["room"] = room
                            ok = True
                        else: ok = False
                    if ok: send(sock, {"type":"ROOM_CHANGED","room":room})
                    else: send(sock, {"type":"ERROR","text":"Room does not exist."})
                elif cmd == "LEAVEROOM":
                    with lock:
                        old = clients[sock]["room"]
                        rooms[old].discard(sock); rooms["General"].add(sock)
                        clients[sock]["room"] = "General"
                    send(sock, {"type":"ROOM_CHANGED","room":"General"})
                elif cmd == "USERS": presence()
                elif cmd == "ROOMS":
                    with lock: names = sorted(rooms)
                    send(sock, {"type":"ROOMS","rooms":names})
                elif cmd == "FILE_OFFER":
                    target = str(p.get("target","")).strip()
                    size = int(p.get("size",0))
                    peer = user_socket(target)
                    if not peer: send(sock, {"type":"ERROR","text":f"{target} is not online."})
                    elif size < 0 or size > MAX_FILE_SIZE: send(sock, {"type":"ERROR","text":"File limit is 100 MB."})
                    else:
                        tid = uuid.uuid4().hex
                        meta = {"id":tid,"sender":name,"target":target,"filename":safe_filename(p.get("filename","file")),"size":size,"ready":False}
                        with lock: files[tid] = meta
                        send(sock, {"type":"FILE_UPLOAD","transfer_id":tid,"size":size})
                        # Recipient is notified only after upload completes.
                elif cmd == "CALL_REQUEST":
                    target = str(p.get("target","")).strip()
                    peer = user_socket(target)
                    if not peer or peer is sock:
                        send(sock, {"type":"ERROR","text":"Select another online user."}); continue
                    cid = uuid.uuid4().hex
                    call = {"id":cid,"caller":name,"receiver":target,"mode":p.get("mode","voice")}
                    with lock: calls[cid] = call
                    send(peer, {"type":"CALL_INCOMING","call_id":cid,"caller":name,"mode":call["mode"]})
                    send(sock, {"type":"CALL_STATUS","call_id":cid,"text":f"{call['mode'].title()} call request sent to {target} (signaling demo only)."})
                elif cmd == "CALL_RESPONSE":
                    cid = str(p.get("call_id",""))
                    with lock: call = calls.get(cid)
                    if not call: send(sock, {"type":"ERROR","text":"Call request expired."}); continue
                    accepted = bool(p.get("accepted"))
                    if not accepted:
                        with lock: calls.pop(cid,None)
                    for person in (call["caller"], call["receiver"]):
                        peer = user_socket(person)
                        if peer: send(peer, {"type":"CALL_STATUS","call_id":cid,"text":f"{name} {'accepted' if accepted else 'rejected'} the {call['mode']} call (signaling only)."})
                elif cmd == "CALL_END":
                    cid = str(p.get("call_id",""))
                    with lock: call = calls.pop(cid,None)
                    if call:
                        for person in (call["caller"],call["receiver"]):
                            peer = user_socket(person)
                            if peer: send(peer, {"type":"CALL_ENDED","call_id":cid,"text":"Call ended."})
                elif cmd == "QUIT":
                    running = False
                    break
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print("[CHAT ERROR]", addr, exc)
    finally:
        remove(sock)
        print("[CHAT DISCONNECTED]", addr)

def read_header(sock):
    data = b""
    while b"\n" not in data:
        chunk = sock.recv(1)
        if not chunk: raise ConnectionError("Transfer connection closed")
        data += chunk
        if len(data)>8192: raise ValueError("Header too long")
    return json.loads(data[:-1].decode("utf-8"))

def handle_transfer(sock, addr):
    try:
        req = read_header(sock)
        tid = str(req.get("transfer_id",""))
        with lock: meta = files.get(tid)
        if req.get("action") == "UPLOAD":
            if not meta or req.get("sender","").casefold() != meta["sender"].casefold() or int(req.get("size",-1)) != meta["size"]:
                sock.sendall(b'{"ok":false,"error":"Transfer metadata mismatch"}\n'); return
            os.makedirs(SAVE_DIR, exist_ok=True)
            path = os.path.join(SAVE_DIR, tid + "_" + safe_filename(meta["filename"]))
            sock.sendall(b'{"ok":true}\n')
            receive_exact(sock, meta["size"], path)
            with lock:
                meta["ready"] = True; meta["path"] = path
            peer = user_socket(meta["target"])
            if peer:
                send(peer, {"type":"FILE_OFFER","transfer_id":tid,"sender":meta["sender"],"filename":meta["filename"],"size":meta["size"]})
            sender = user_socket(meta["sender"])
            if sender: send(sender, {"type":"FILE_SENT","filename":meta["filename"],"target":meta["target"]})
        elif req.get("action") == "DOWNLOAD":
            if not meta or not meta["ready"] or req.get("username","").casefold() != meta["target"].casefold():
                sock.sendall(b'{"ok":false,"error":"File unavailable or not addressed to you"}\n'); return
            sock.sendall((json.dumps({"ok":True,"filename":meta["filename"],"size":meta["size"]})+"\n").encode())
            with open(meta["path"],"rb") as f:
                while True:
                    chunk=f.read(4096)
                    if not chunk: break
                    sock.sendall(chunk)
            with lock: files.pop(tid,None)
        else:
            sock.sendall(b'{"ok":false,"error":"Unknown transfer action"}\n')
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print("[FILE ERROR]", addr, exc)
    finally:
        try: sock.close()
        except OSError: pass

def transfer_server():
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM); s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    s.bind((HOST,FILE_PORT)); s.listen(20)
    print("[FILE SERVER READY]", FILE_PORT)
    while True:
        c,a=s.accept(); threading.Thread(target=handle_transfer,args=(c,a),daemon=True).start()

def main():
    threading.Thread(target=transfer_server,daemon=True).start()
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM); s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    s.bind((HOST,CHAT_PORT)); s.listen(20)
    print(f"[SERVER READY] Chat TCP {CHAT_PORT}; file TCP {FILE_PORT}")
    try:
        while True:
            c,a=s.accept(); threading.Thread(target=handle_client,args=(c,a),daemon=True).start()
    except KeyboardInterrupt: print("\n[SERVER STOPPING]")
    finally: s.close()

if __name__ == "__main__": main()
