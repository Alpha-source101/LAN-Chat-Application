import os, queue, socket, threading, tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
from client import ChatClient

BG="#f2f5fb"; BLUE="#245fd3"; INK="#1e293b"; MUTED="#64748b"

class LANChatGUI:
    def __init__(self,root):
        self.root=root; self.root.title("LAN Chat Application"); self.root.geometry("1000x760")
        self.root.minsize(820,650); self.root.configure(bg=BG)
        self.events=queue.Queue(); self.client=None; self.username=""; self.current_room="General"
        self.private_target=None; self.users=[]; self.rooms=["General"]; self.pending_calls={}
        self.pending_uploads={}
        self.build()
        self.connected(False)
        self.root.after(100,self.process_events)
        self.root.protocol("WM_DELETE_WINDOW",self.close)

    def build(self):
        style=ttk.Style()
        try: style.theme_use("clam")
        except tk.TclError: pass
        style.configure("TButton",font=("Segoe UI",10),padding=5)
        style.configure("TLabel",background=BG,foreground=INK,font=("Segoe UI",10))
        style.configure("Title.TLabel",font=("Segoe UI",20,"bold"),foreground=BLUE)
        ttk.Label(self.root,text="LAN Chat Application",style="Title.TLabel").pack(pady=(14,8))
        bar=ttk.Frame(self.root,padding=10); bar.pack(fill="x",padx=18,pady=4)
        ttk.Label(bar,text="Server IP:").pack(side="left")
        self.host=ttk.Entry(bar,width=16); self.host.insert(0,"127.0.0.1"); self.host.pack(side="left",padx=5)
        ttk.Label(bar,text="Username:").pack(side="left",padx=(10,0))
        self.name=ttk.Entry(bar,width=16); self.name.insert(0,"Student"); self.name.pack(side="left",padx=5)
        self.join_btn=ttk.Button(bar,text="Join Chat",command=self.join); self.join_btn.pack(side="left",padx=(10,3))
        self.leave_btn=ttk.Button(bar,text="Leave Chat",command=self.leave); self.leave_btn.pack(side="left",padx=3)

        main=ttk.Frame(self.root); main.pack(fill="both",expand=True,padx=18,pady=6)
        side=ttk.Frame(main,padding=10); side.pack(side="left",fill="y",padx=(0,8))
        ttk.Label(side,text="Chat Rooms",font=("Segoe UI",11,"bold")).pack(anchor="w")
        self.room_list=tk.Listbox(side,height=7,width=23,exportselection=False,relief="flat")
        self.room_list.pack(fill="x",pady=5); self.room_list.insert("end","General")
        row=ttk.Frame(side); row.pack(fill="x",pady=(2,4))
        self.room_entry=ttk.Entry(row,width=13); self.room_entry.insert(0,"NewRoom")
        self.room_entry.pack(side="left",fill="x",expand=True)
        self.create_btn=ttk.Button(row,text="Create",command=self.create_room); self.create_btn.pack(side="left",padx=2)
        self.join_room_btn=ttk.Button(side,text="Join Selected",command=self.join_room); self.join_room_btn.pack(fill="x",pady=(0,12))
        ttk.Label(side,text="Active Users (Online)",font=("Segoe UI",11,"bold")).pack(anchor="w")
        self.user_list=tk.Listbox(side,height=11,width=23,exportselection=False,relief="flat")
        self.user_list.pack(fill="x",pady=5)
        self.private_btn=ttk.Button(side,text="Private Chat",command=self.private_chat); self.private_btn.pack(fill="x",pady=2)
        self.group_btn=ttk.Button(side,text="Back to Group",command=self.back_group); self.group_btn.pack(fill="x",pady=2)

        panel=ttk.Frame(main,padding=10); panel.pack(side="left",fill="both",expand=True)
        self.target=ttk.Label(panel,text="Current: Room 'General'",font=("Segoe UI",11,"bold")); self.target.pack(anchor="w",pady=(0,7))
        chat_frame=ttk.Frame(panel); chat_frame.pack(fill="both",expand=True)
        self.chat=tk.Text(chat_frame,wrap="word",state="disabled",font=("Segoe UI",10),bg="white",fg=INK,relief="flat",padx=10,pady=10)
        scroll=ttk.Scrollbar(chat_frame,command=self.chat.yview); self.chat.configure(yscrollcommand=scroll.set)
        self.chat.pack(side="left",fill="both",expand=True); scroll.pack(side="right",fill="y")
        self.chat.tag_configure("system",foreground=MUTED); self.chat.tag_configure("private",foreground="#9147b6")
        self.status=ttk.Label(panel,text="Not connected"); self.status.pack(anchor="w",pady=(5,2))
        tools=ttk.Frame(panel); tools.pack(fill="x",pady=5)
        ttk.Label(tools,text="Attach:").pack(side="left",padx=(0,4))
        self.file_btn=ttk.Button(tools,text="File",command=lambda:self.attach("file")); self.file_btn.pack(side="left",padx=2)
        self.image_btn=ttk.Button(tools,text="Image",command=lambda:self.attach("image")); self.image_btn.pack(side="left",padx=2)
        self.video_btn=ttk.Button(tools,text="Video",command=lambda:self.attach("video")); self.video_btn.pack(side="left",padx=2)
        ttk.Label(tools,text="Calls:").pack(side="left",padx=(12,4))
        self.voice_btn=ttk.Button(tools,text="Voice Call",command=lambda:self.start_call("voice")); self.voice_btn.pack(side="left",padx=2)
        self.video_call_btn=ttk.Button(tools,text="Video Call",command=lambda:self.start_call("video")); self.video_call_btn.pack(side="left",padx=2)
        row=ttk.Frame(panel); row.pack(fill="x",pady=(5,0))
        self.message=ttk.Entry(row); self.message.pack(side="left",fill="x",expand=True,padx=(0,7),ipady=4)
        self.message.bind("<Return>",lambda e:self.send_message())
        self.send_btn=ttk.Button(row,text="Send",command=self.send_message); self.send_btn.pack(side="right")

    def connected(self,yes):
        self.join_btn.configure(state="disabled" if yes else "normal")
        self.leave_btn.configure(state="normal" if yes else "disabled")
        self.host.configure(state="disabled" if yes else "normal")
        self.name.configure(state="disabled" if yes else "normal")
        for w in (self.room_entry,self.create_btn,self.join_room_btn,self.private_btn,self.group_btn,
                  self.file_btn,self.image_btn,self.video_btn,self.voice_btn,self.video_call_btn,self.message,self.send_btn):
            w.configure(state="normal" if yes else "disabled")
        self.status.configure(text="Connected" if yes else "Not connected")

    def log(self,text,tag=""):
        stamp=datetime.now().strftime("%I:%M:%S %p")
        self.chat.configure(state="normal"); self.chat.insert("end",f"[{stamp}] {text}\n",tag)
        self.chat.see("end"); self.chat.configure(state="disabled")

    def join(self):
        host=self.host.get().strip(); name=self.name.get().strip()
        if not host or not name: messagebox.showwarning("Required","Enter server IP and username."); return
        try:
            self.client=ChatClient(host,callback=self.events.put); self.client.connect(name)
            self.username=name; self.connected(True); self.log("Connecting to server...","system")
        except OSError as exc:
            self.client=None; messagebox.showerror("Connection failed",str(exc))

    def leave(self):
        if self.client: self.client.close()
        self.client=None; self.connected(False); self.private_target=None; self.current_room="General"
        self.target.configure(text="Current: Room 'General'"); self.log("You left the chat.","system")

    def send_message(self):
        text=self.message.get().strip()
        if not text or not self.client or not self.client.connected: return
        if self.private_target: self.client.private(self.private_target,text)
        else: self.client.public(text)
        self.message.delete(0,"end")

    def create_room(self):
        room=self.room_entry.get().strip()
        if room and self.client: self.client.create_room(room)

    def join_room(self):
        selected=self.room_list.curselection()
        if not selected or not self.client: messagebox.showinfo("Select room","Choose a room first."); return
        self.client.join_room(self.room_list.get(selected[0]))

    def private_chat(self):
        selected=self.user_list.curselection()
        if not selected: messagebox.showinfo("Select user","Choose an online user."); return
        target=self.user_list.get(selected[0])
        if target==self.username: messagebox.showinfo("Select user","Choose another user."); return
        self.private_target=target; self.target.configure(text=f"Current: Private Chat with '{target}'")
        self.log(f"Private chat selected with {target}.","system")

    def back_group(self):
        self.private_target=None; self.target.configure(text=f"Current: Room '{self.current_room}'")
        self.log("Returned to group chat.","system")

    def attach(self,kind):
        if not self.client or not self.client.connected: return
        selected=self.user_list.curselection()
        target=self.private_target or (self.user_list.get(selected[0]) if selected else "")
        if not target or target==self.username:
            messagebox.showinfo("Recipient","Select another online user before sending a file."); return
        filters={"file":[("All files","*.*")],"image":[("Images","*.png *.jpg *.jpeg *.gif *.bmp *.webp")],
                 "video":[("Videos","*.mp4 *.avi *.mkv *.mov *.webm")]}
        path=filedialog.askopenfilename(title="Choose "+kind,filetypes=filters[kind])
        if not path: return
        size=os.path.getsize(path)
        if size>100*1024*1024: messagebox.showerror("File too large","Maximum file size is 100 MB."); return
        self.client.pending_path=path
        self.client.offer_file(target,path)
        self.log(f"Preparing {os.path.basename(path)} for {target}.","system")

    def start_call(self,mode):
        selected=self.user_list.curselection()
        if not self.client or not selected: messagebox.showinfo("Choose user","Select an online user first."); return
        target=self.user_list.get(selected[0])
        if target==self.username: messagebox.showinfo("Choose user","Choose another user."); return
        self.client.call(target,mode)

    def process_events(self):
        try:
            while True:
                e=self.events.get_nowait(); kind=e.get("type")
                if kind=="USERS":
                    self.users=e.get("users",[]); self.user_list.delete(0,"end")
                    for u in self.users: self.user_list.insert("end",u)
                elif kind=="ROOMS":
                    self.rooms=e.get("rooms",["General"]); self.room_list.delete(0,"end")
                    for r in self.rooms: self.room_list.insert("end",r)
                elif kind=="JOINED":
                    self.username=e.get("username",self.username); self.log(f"Welcome, {self.username}!","system")
                elif kind=="INFO": self.log(e.get("text",""),"system")
                elif kind=="ERROR":
                    self.log("Error: "+e.get("text","Unknown error"),"system"); self.status.configure(text=e.get("text","Error"))
                elif kind=="ROOM_CHANGED":
                    self.current_room=e.get("room","General"); self.private_target=None
                    self.target.configure(text=f"Current: Room '{self.current_room}'"); self.log(f"Switched to {self.current_room}.","system")
                elif kind=="ROOMMSG": self.log(f"[{e.get('room')}] {e.get('sender')}: {e.get('text')}")
                elif kind=="PRV": self.log(f"[Private] {e.get('sender')}: {e.get('text')}","private")
                elif kind=="FILE_UPLOAD":
                    path=getattr(self.client,"pending_path",None)
                    if path:
                        threading.Thread(target=self.client.upload,args=(e["transfer_id"],e["size"],path),daemon=True).start()
                    else: self.log("File upload cancelled: file path unavailable.","system")
                elif kind=="FILE_OFFER":
                    accepted=messagebox.askyesno("Incoming file",f"{e['sender']} sent {e['filename']} ({e['size']} bytes). Download it?")
                    if accepted: threading.Thread(target=self.client.download,args=(e["transfer_id"],),daemon=True).start()
                    else: self.log(f"Declined {e['filename']}.","system")
                elif kind=="FILE_SENT": self.log(f"Sent {e['filename']} to {e['target']}.","system")
                elif kind=="FILE_RECEIVED":
                    self.log(f"Received {e['filename']} -> {e['path']}","system")
                    messagebox.showinfo("File received",f"Saved to:\n{e['path']}")
                elif kind=="CALL_INCOMING":
                    yes=messagebox.askyesno("Incoming call",f"{e['caller']} requests a {e['mode']} call.\nAccept? (Signaling demo; no media stream)")
                    if self.client: self.client.respond(e["call_id"],yes)
                elif kind=="CALL_STATUS": self.log(e.get("text",""),"system"); self.status.configure(text=e.get("text",""))
                elif kind=="CALL_ENDED": self.log("Call ended.","system")
                elif kind=="DISCONNECTED":
                    self.connected(False); self.status.configure(text="Disconnected")
        except queue.Empty: pass
        if self.root.winfo_exists(): self.root.after(100,self.process_events)

    def close(self):
        if self.client: self.client.close()
        self.root.destroy()

if __name__=="__main__":
    root=tk.Tk(); LANChatGUI(root); root.mainloop()
