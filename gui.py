import socket
import threading
import json
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

class ClientBuffer:
    def __init__(self):
        self.buffer = b""
    def feed(self, data):
        self.buffer += data
        packets = []
        while b"\n" in self.buffer:
            line, self.buffer = self.buffer.split(b"\n", 1)
            if line.strip():
                try:
                    packets.append(json.loads(line.decode("utf-8")))
                except json.JSONDecodeError:
                    pass
        return packets

class LANChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("LAN Chat Application")
        self.root.geometry("1100x750")
        self.root.configure(bg="#F8FAFC")

        self.sock = None
        self.connected = False
        self.current_username = ""
        self.current_room = "General"
        self.target_user = None  # Private chat ke liye

        self.setup_ui()

    def setup_ui(self):
        # --- Top Connection Bar ---
        top_frame = tk.Frame(self.root, bg="#FFFFFF", height=60)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        top_frame.pack_propagate(False)

        tk.Label(top_frame, text="Server IP:", bg="#FFFFFF", fg="#1E293B", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(15, 5))
        self.ip_input = tk.Entry(top_frame, font=("Segoe UI", 10), bd=1, relief="solid")
        self.ip_input.insert(0, "127.0.0.1")
        self.ip_input.pack(side=tk.LEFT, padx=5, ipadx=5, ipady=3)

        tk.Label(top_frame, text="Username:", bg="#FFFFFF", fg="#1E293B", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(15, 5))
        self.username_input = tk.Entry(top_frame, font=("Segoe UI", 10), bd=1, relief="solid")
        self.username_input.insert(0, "Student")
        self.username_input.pack(side=tk.LEFT, padx=5, ipadx=5, ipady=3)

        self.join_btn = tk.Button(top_frame, text="Join Chat", bg="#2563EB", fg="white", font=("Segoe UI", 10, "bold"), bd=0, padx=15, pady=5, cursor="hand2", command=self.connect_to_server)
        self.join_btn.pack(side=tk.LEFT, padx=10)

        self.leave_btn = tk.Button(top_frame, text="Leave Chat", bg="#F1F5F9", fg="#475569", font=("Segoe UI", 10), bd=1, relief="solid", padx=15, pady=5, cursor="hand2", command=self.disconnect_from_server)
        self.leave_btn.pack(side=tk.LEFT, padx=5)

        ttk.Separator(self.root, orient="horizontal").pack(fill=tk.X)

        # --- Main Body Layout ---
        main_container = tk.Frame(self.root, bg="#F8FAFC")
        main_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Left Sidebar
        sidebar = tk.Frame(main_container, bg="#FFFFFF", width=280)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="Chat Rooms", bg="#FFFFFF", fg="#1E293B", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=15, pady=(15, 5))
        
        self.rooms_list = tk.Listbox(sidebar, font=("Segoe UI", 10), bg="#FFFFFF", fg="#334155", bd=1, relief="solid", highlightthickness=0)
        self.rooms_list.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        self.rooms_list.insert(tk.END, "General")

        room_bottom_frame = tk.Frame(sidebar, bg="#FFFFFF")
        room_bottom_frame.pack(fill=tk.X, padx=15, pady=5)
        
        self.new_room_input = tk.Entry(room_bottom_frame, font=("Segoe UI", 9), bd=1, relief="solid")
        self.new_room_input.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3, padx=(0, 5))
        
        self.create_room_btn = tk.Button(room_bottom_frame, text="Create", bg="#2563EB", fg="white", font=("Segoe UI", 9, "bold"), bd=0, padx=10, pady=2, command=self.create_room)
        self.create_room_btn.pack(side=tk.RIGHT)

        self.join_room_btn = tk.Button(sidebar, text="Join Selected Room", bg="#F1F5F9", fg="#475569", font=("Segoe UI", 9), bd=1, relief="solid", pady=4, command=self.join_room)
        self.join_room_btn.pack(fill=tk.X, padx=15, pady=5)

        tk.Label(sidebar, text="Active Users (Online)", bg="#FFFFFF", fg="#1E293B", font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=15, pady=(15, 5))
        
        self.users_list = tk.Listbox(sidebar, font=("Segoe UI", 10), bg="#FFFFFF", fg="#334155", bd=1, relief="solid", highlightthickness=0)
        self.users_list.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        self.private_chat_btn = tk.Button(sidebar, text="Private Chat", bg="#F1F5F9", fg="#475569", font=("Segoe UI", 9), bd=1, relief="solid", pady=4, command=self.start_private_chat)
        self.private_chat_btn.pack(fill=tk.X, padx=15, pady=(5, 2))

        self.back_group_btn = tk.Button(sidebar, text="Back to Group", bg="#F1F5F9", fg="#475569", font=("Segoe UI", 9), bd=1, relief="solid", pady=4, command=self.leave_room)
        self.back_group_btn.pack(fill=tk.X, padx=15, pady=(2, 15))

        # Right Chat Area
        chat_area = tk.Frame(main_container, bg="#F8FAFC")
        chat_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=15, pady=15)

        self.room_title_label = tk.Label(chat_area, text="Current: Room 'General'", bg="#F8FAFC", fg="#1E293B", font=("Segoe UI", 11, "bold"))
        self.room_title_label.pack(anchor="w", pady=(0, 10))

        self.chat_display = scrolledtext.ScrolledText(chat_area, font=("Segoe UI", 10), bg="#FFFFFF", fg="#1E293B", bd=1, relief="solid", state="normal")
        self.chat_display.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Bottom Action Bar
        action_bar = tk.Frame(chat_area, bg="#F8FAFC")
        action_bar.pack(fill=tk.X, pady=(0, 10))

        self.status_label = tk.Label(action_bar, text="Disconnected", bg="#F8FAFC", fg="#DC2626", font=("Segoe UI", 9, "bold"))
        self.status_label.pack(side=tk.LEFT)

        msg_box_frame = tk.Frame(chat_area, bg="#F8FAFC")
        msg_box_frame.pack(fill=tk.X)

        self.message_input = tk.Entry(msg_box_frame, font=("Segoe UI", 11), bg="#FFFFFF", fg="#1E293B", bd=1, relief="solid")
        self.message_input.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 10))
        self.message_input.bind("<Return>", lambda event: self.send_message())

        self.send_btn = tk.Button(msg_box_frame, text="Send", bg="#2563EB", fg="white", font=("Segoe UI", 10, "bold"), bd=0, padx=20, pady=8, cursor="hand2", command=self.send_message)
        self.send_btn.pack(side=tk.RIGHT)

    def send_packet(self, packet):
        if self.sock and self.connected:
            try:
                data = (json.dumps(packet) + "\n").encode("utf-8")
                self.sock.sendall(data)
            except Exception as e:
                print("Send error:", e)

    def connect_to_server(self):
        if self.connected:
            return
        ip = self.ip_input.get().strip()
        username = self.username_input.get().strip()
        if not ip or not username:
            messagebox.showerror("Error", "Please enter Server IP and Username.")
            return
        
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((ip, 5000))
            self.connected = True
            self.current_username = username

            # Receive thread start karo
            threading.Thread(target=self.receive_loop, daemon=True).start()

            # Join request bhejo
            self.send_packet({"type": "JOIN", "username": username})
        except Exception as e:
            messagebox.showerror("Connection Error", f"Could not connect to server: {e}")
            self.connected = False

    def disconnect_from_server(self):
        if not self.connected:
            return
        try:
            self.send_packet({"type": "QUIT"})
            self.sock.close()
        except:
            pass
        self.connected = False
        self.status_label.config(text="Disconnected", fg="#DC2626")
        self.append_info("Disconnected from server.")

    def receive_loop(self):
        buffer = ClientBuffer()
        while self.connected:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break
                for packet in buffer.feed(data):
                    self.handle_packet(packet)
            except Exception as e:
                print("Receive error:", e)
                break
        self.connected = False
        self.root.after(0, lambda: self.status_label.config(text="Disconnected", fg="#DC2626"))

    def handle_packet(self, p):
        ptype = p.get("type")
        if ptype == "JOINED":
            self.root.after(0, lambda: self.status_label.config(text=f"Connected as {p.get('username')}", fg="#16A34A"))
            self.append_info(f"Welcome, {p.get('username')}!")
        elif ptype == "INFO":
            self.append_info(p.get("text"))
        elif ptype == "ERROR":
            messagebox.showerror("Server Error", p.get("text"))
        elif ptype == "USERS":
            users = p.get("users", [])
            self.root.after(0, lambda: self.update_users_list(users))
        elif ptype == "ROOMS":
            rooms = p.get("rooms", [])
            self.root.after(0, lambda: self.update_rooms_list(rooms))
        elif ptype == "ROOMMSG":
            sender = p.get("sender")
            text = p.get("text")
            room = p.get("room")
            self.root.after(0, lambda: self.append_message(f"[{room}] {sender}", text))
        elif ptype == "PRV":
            sender = p.get("sender")
            target = p.get("target")
            text = p.get("text")
            display_name = sender if sender.casefold() != self.current_username.casefold() else f"to {target}"
            self.append_message(f"[Private] {display_name}", text)
        elif ptype == "ROOM_CHANGED":
            room = p.get("room")
            self.current_room = room
            self.target_user = None
            self.root.after(0, lambda: self.room_title_label.config(text=f"Current: Room '{room}'"))
            self.append_info(f"Joined room '{room}'")

    def update_users_list(self, users):
        self.users_list.delete(0, tk.END)
        for u in users:
            self.users_list.insert(tk.END, u)

    def update_rooms_list(self, rooms):
        self.rooms_list.delete(0, tk.END)
        for r in rooms:
            self.rooms_list.insert(tk.END, r)

    def send_message(self):
        if not self.connected:
            messagebox.showwarning("Not Connected", "Please join the chat first.")
            return
        text = self.message_input.get().strip()
        if not text:
            return
        
        if self.target_user:
            self.send_packet({"type": "PRV", "target": self.target_user, "text": text})
        else:
            self.send_packet({"type": "MSG", "text": text})
        
        self.message_input.delete(0, tk.END)

    def create_room(self):
        room_name = self.new_room_input.get().strip()
        if room_name:
            self.send_packet({"type": "CREATE", "room": room_name})
            self.new_room_input.delete(0, tk.END)

    def join_room(self):
        try:
            selected_indices = self.rooms_list.curselection()
            if selected_indices:
                room_name = self.rooms_list.get(selected_indices[0])
                self.send_packet({"type": "JOINROOM", "room": room_name})
                self.target_user = None
        except Exception as e:
            print(e)

        def leave_room(self):
            self.send_packet({"type": "LEAVEROOM"})
            self.target_user = None

    def leave_room(self):
        self.send_packet({"type": "LEAVEROOM"})
        self.target_user = None

    def start_private_chat(self):
        try:
            selected_indices = self.users_list.curselection()
            if selected_indices:
                username = self.users_list.get(selected_indices[0])
                if username.casefold() == self.current_username.casefold():
                    messagebox.showwarning("Invalid", "Aap khud ke sath private chat nahi kar sakte.")
                    return
                self.target_user = username
                self.room_title_label.config(text=f"Private Chat with: {username}")
                self.append_info(f"Switched to private chat with {username}")
        except Exception as e:
            print(e)

    def append_message(self, sender, text):
        formatted_msg = f"\n{sender}: {text}\n"
        self.chat_display.insert(tk.END, formatted_msg)
        self.chat_display.see(tk.END)

    def append_info(self, text):
        self.chat_display.insert(tk.END, f"\n--- {text} ---\n")
        self.chat_display.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = LANChatClient(root)
    root.mainloop()