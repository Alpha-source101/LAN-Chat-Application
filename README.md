# LAN Chat Application — integrated build

## Run
1. Run `python server.py` on the host computer.
2. Run `python gui.py` on each client computer.
3. On the host itself use Server IP `127.0.0.1`. On other LAN computers, enter the host's IPv4 address.
4. Allow TCP ports 5000 and 5001 through the host firewall.

## Features
- Server-managed group chat, rooms, private messages, active users.
- Tkinter GUI based on the team's screenshot layout.
- File/image/video transfer over a separate TCP connection, 4096-byte binary chunks, 100 MB maximum.
- Voice/video call request/accept/reject signaling workflow. No actual microphone or camera media streaming.
- Received files go to `received_files/`; server copies go to `server_received/`.

## Protocol
Control messages use newline-delimited JSON to preserve message boundaries and Unicode. File bytes are sent separately and are never decoded as text.

## Current limits
Voice note recording and actual audio/video streaming are not implemented. Test on the target computers and LAN before submission. This is a course-project integration build, not a security-hardened production messenger.
