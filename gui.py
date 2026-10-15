import os
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, filedialog

root = tk.Tk()
root.title("LAN Chat Application")
root.geometry("680x750")

# Heading
heading = tk.Label(
    root,
    text="LAN Chat Application",
    font=("Arial", 18, "bold")
)
heading.pack(pady=10)

# Global variables (Rooms, Active Users, Current Chat target)
current_chat_target = "General"
is_private = False
rooms = ["General"]
active_users = []

# ----------------- Connection Section -----------------
user_frame = tk.Frame(root)
user_frame.pack(pady=5)

username_label = tk.Label(user_frame, text="Username:", font=("Arial", 11))
username_label.pack(side="left", padx=5)

username_entry = tk.Entry(user_frame, font=("Arial", 11), width=18)
username_entry.insert(0, "Student")
username_entry.pack(side="left", padx=5)

# Button click hone par yeh function chalega
def join_chat():
    username = username_entry.get().strip()
    if username == "":
        messagebox.showwarning("Warning", "Please enter your username!")
    else:
        messagebox.showinfo("Welcome", f"Welcome to LAN Chat, {username}!")
        message_entry.config(state="normal")
        send_button.config(state="normal")
        join_button.config(state="disabled")
        username_entry.config(state="disabled")

        # Chat join hone par active user list main add hoga
        if username not in active_users:
            active_users.append(username)
            users_list.insert("end", username)

        chat_area.config(state="normal")
        chat_area.insert("end", f"[System]: Welcome {username}! You joined '{current_chat_target}'.\n")
        chat_area.config(state="disabled")

def leave_chat():
    username = username_entry.get().strip()
    if username in active_users:
        active_users.remove(username)
        users_list.delete(0, "end")
        for u in active_users:
            users_list.insert("end", u)

    message_entry.config(state="disabled")
    send_button.config(state="disabled")
    username_entry.config(state="normal")
    join_button.config(state="normal")

    chat_area.config(state="normal")
    chat_area.insert("end", "[System]: You left the chat.\n")
    chat_area.config(state="disabled")

# Join Chat button
join_button = tk.Button(
    user_frame,
    text="Join Chat",
    command=join_chat,
    font=("Arial", 10, "bold")
)
join_button.pack(side="left", padx=5)

# Leave Chat button
leave_button = tk.Button(
    user_frame,
    text="Leave Chat",
    font=("Arial", 10),
    command=leave_chat
)
leave_button.pack(side="left", padx=5)


# ----------------- Rooms aur Active Users (Group / Private) -----------------
rooms_users_frame = tk.Frame(root)
rooms_users_frame.pack(pady=5, fill="x", padx=30)

# Left Side: Chat Rooms
room_col = tk.Frame(rooms_users_frame)
room_col.pack(side="left", expand=True, fill="both", padx=5)

tk.Label(room_col, text="Chat Rooms:", font=("Arial", 10, "bold")).pack(anchor="w")
rooms_list = tk.Listbox(room_col, height=4)
for r in rooms:
    rooms_list.insert("end", r)
rooms_list.pack(fill="x", pady=2)

room_input_frame = tk.Frame(room_col)
room_input_frame.pack(fill="x", pady=2)

new_room_entry = tk.Entry(room_input_frame, width=12)
new_room_entry.insert(0, "NewRoom")
new_room_entry.pack(side="left", fill="x", expand=True)

def create_room():
    if username_entry.cget("state") != "disabled":
        messagebox.showwarning("Warning", "Join Chat first!")
        return
    new_r = new_room_entry.get().strip()
    if new_r and new_r not in rooms:
        rooms.append(new_r)
        rooms_list.insert("end", new_r)
        new_room_entry.delete(0, "end")
        chat_area.config(state="normal")
        chat_area.insert("end", f"[System]: Room '{new_r}' created!\n")
        chat_area.config(state="disabled")

def join_room():
    global current_chat_target, is_private
    if username_entry.cget("state") != "disabled":
        messagebox.showwarning("Warning", "Join Chat first!")
        return
    selection = rooms_list.curselection()
    if selection:
        selected_room = rooms_list.get(selection[0])
        current_chat_target = selected_room
        is_private = False
        target_label.config(text=f"Current: Room '{current_chat_target}'")
        chat_area.config(state="normal")
        chat_area.insert("end", f"[System]: Switched to Room '{current_chat_target}'.\n")
        chat_area.config(state="disabled")

tk.Button(room_input_frame, text="Create", command=create_room, font=("Arial", 9)).pack(side="left", padx=2)
tk.Button(room_input_frame, text="Join", command=join_room, font=("Arial", 9)).pack(side="left", padx=2)

# Right Side: Active Users (Private Chat)
user_col = tk.Frame(rooms_users_frame)
user_col.pack(side="right", expand=True, fill="both", padx=5)

tk.Label(user_col, text="Active Users (Online):", font=("Arial", 10, "bold")).pack(anchor="w")
users_list = tk.Listbox(user_col, height=4)
for u in active_users:
    users_list.insert("end", u)
users_list.pack(fill="x", pady=2)

def start_private_chat():
    global current_chat_target, is_private
    if username_entry.cget("state") != "disabled":
        messagebox.showwarning("Warning", "Join Chat first!")
        return
    selection = users_list.curselection()
    if selection:
        selected_user = users_list.get(selection[0])
        current_chat_target = selected_user
        is_private = True
        target_label.config(text=f"Current: Private Chat with '{current_chat_target}'")
        chat_area.config(state="normal")
        chat_area.insert("end", f"[System]: Private chat with {current_chat_target} started.\n")
        chat_area.config(state="disabled")

def back_to_group():
    global current_chat_target, is_private
    current_chat_target = "General"
    is_private = False
    target_label.config(text=f"Current: Room 'General'")
    chat_area.config(state="normal")
    chat_area.insert("end", f"[System]: Returned to General room.\n")
    chat_area.config(state="disabled")

user_btn_row = tk.Frame(user_col)
user_btn_row.pack(fill="x", pady=2)
tk.Button(user_btn_row, text="Private Chat", command=start_private_chat, font=("Arial", 9)).pack(side="left", expand=True, fill="x")
tk.Button(user_btn_row, text="Back to Group", command=back_to_group, font=("Arial", 9)).pack(side="right", expand=True, fill="x", padx=(2, 0))


# ----------------- Calling & Current Target Bar -----------------
call_bar = tk.Frame(root)
call_bar.pack(pady=4, fill="x", padx=30)

target_label = tk.Label(call_bar, text=f"Current: Room '{current_chat_target}'", font=("Arial", 10, "bold"), fg="blue")
target_label.pack(side="left")

def voice_call():
    if username_entry.cget("state") != "disabled":
        messagebox.showwarning("Warning", "Join Chat first!")
        return
    messagebox.showinfo("Voice Call", f"Calling {current_chat_target} (Voice Call Connected!)")
    chat_area.config(state="normal")
    chat_area.insert("end", f"[Call]: Voice call started with {current_chat_target}.\n")
    chat_area.config(state="disabled")

def video_call():
    if username_entry.cget("state") != "disabled":
        messagebox.showwarning("Warning", "Join Chat first!")
        return
    messagebox.showinfo("Video Call", f"Calling {current_chat_target} (Video Call Connected!)")
    chat_area.config(state="normal")
    chat_area.insert("end", f"[Call]: Video call started with {current_chat_target}.\n")
    chat_area.config(state="disabled")

tk.Button(call_bar, text="Video Call", command=video_call, font=("Arial", 9, "bold")).pack(side="right", padx=3)
tk.Button(call_bar, text="Voice Call", command=voice_call, font=("Arial", 9, "bold")).pack(side="right", padx=3)


# ----------------- Chat Area Display -----------------
chat_frame = tk.Frame(root)
chat_frame.pack(pady=5, padx=30, fill="both", expand=True)

chat_scroll = tk.Scrollbar(chat_frame)
chat_scroll.pack(side="right", fill="y")

# Chat messages display area
chat_area = tk.Text(
    chat_frame,
    height=11,
    width=55,
    state="disabled",
    yscrollcommand=chat_scroll.set
)
chat_area.pack(side="left", fill="both", expand=True)
chat_scroll.config(command=chat_area.yview)


# ----------------- Media / File Sharing Toolbar -----------------
media_bar = tk.Frame(root)
media_bar.pack(pady=3)

def send_file():
    if username_entry.cget("state") != "disabled":
        messagebox.showwarning("Warning", "Join Chat first!")
        return
    file_path = filedialog.askopenfilename(title="Select File", filetypes=[("All Files", "*.*")])
    if file_path:
        file_name = os.path.basename(file_path)
        chat_area.config(state="normal")
        chat_area.insert("end", f"[{datetime.now().strftime('%I:%M %p')}] {username_entry.get()}: [Sent File: {file_name}]\n")
        chat_area.config(state="disabled")

def send_image():
    if username_entry.cget("state") != "disabled":
        messagebox.showwarning("Warning", "Join Chat first!")
        return
    file_path = filedialog.askopenfilename(title="Select Image", filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif")])
    if file_path:
        file_name = os.path.basename(file_path)
        chat_area.config(state="normal")
        chat_area.insert("end", f"[{datetime.now().strftime('%I:%M %p')}] {username_entry.get()}: [Sent Image: {file_name}]\n")
        chat_area.config(state="disabled")

def send_video():
    if username_entry.cget("state") != "disabled":
        messagebox.showwarning("Warning", "Join Chat first!")
        return
    file_path = filedialog.askopenfilename(title="Select Video", filetypes=[("Video Files", "*.mp4 *.avi *.mkv")])
    if file_path:
        file_name = os.path.basename(file_path)
        chat_area.config(state="normal")
        chat_area.insert("end", f"[{datetime.now().strftime('%I:%M %p')}] {username_entry.get()}: [Sent Video: {file_name}]\n")
        chat_area.config(state="disabled")

def send_voice_note():
    if username_entry.cget("state") != "disabled":
        messagebox.showwarning("Warning", "Join Chat first!")
        return
    messagebox.showinfo("Voice Message", "Voice Note (0:05 sec) recorded.")
    chat_area.config(state="normal")
    chat_area.insert("end", f"[{datetime.now().strftime('%I:%M %p')}] {username_entry.get()}: [Voice Note 0:05 sec]\n")
    chat_area.config(state="disabled")

tk.Label(media_bar, text="Attach:", font=("Arial", 9, "bold")).pack(side="left", padx=4)
tk.Button(media_bar, text="File", command=send_file, font=("Arial", 9)).pack(side="left", padx=3)
tk.Button(media_bar, text="Image", command=send_image, font=("Arial", 9)).pack(side="left", padx=3)
tk.Button(media_bar, text="Video", command=send_video, font=("Arial", 9)).pack(side="left", padx=3)
tk.Button(media_bar, text="Voice Note", command=send_voice_note, font=("Arial", 9)).pack(side="left", padx=3)


# ----------------- Message Input & Send Button -----------------
input_row = tk.Frame(root)
input_row.pack(pady=8, padx=30, fill="x")

# Message likhne ka input box
message_entry = tk.Entry(
    input_row,
    font=("Arial", 11),
    state="disabled"
)
message_entry.pack(side="left", fill="x", expand=True, padx=(0, 6), ipady=3)

# yeah input box sa message la ka chat box main display kara ga.
def send_message():
    message = message_entry.get().strip()

    if message != "":
        chat_area.config(state="normal")
        current_time = datetime.now().strftime("%I:%M %p")
        chat_area.insert("end", f"[{current_time}] {username_entry.get()}: {message}\n")
        chat_area.see("end")
        chat_area.config(state="disabled")
        message_entry.delete(0, "end")

# Send Message button
send_button = tk.Button(
    input_row,
    text="Send",
    command=send_message,
    font=("Arial", 11, "bold"),
    state="disabled",
    width=8
)
send_button.pack(side="right")

# yeah enter button press karna par bhi message jaya ga
message_entry.bind("<Return>", lambda event: send_message())

root.mainloop()

# yeah code ha sara daikh la ab