import socket
import json
import time

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5005

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    print(f"[Server] Listening on {SERVER_IP}:{SERVER_PORT}")

    sessions = {}

    while True:
        data, addr = server_socket.recvfrom(1024)
        message = json.loads(data.decode())

        print(f"[Server] Received: {message} from {addr}")
        if 'timestamp' in message:
            print(f"   ↳ Timestamp: {message['timestamp']} ({time.ctime(message['timestamp'])})")

        msg_type = message.get("type")

        if msg_type == "INIT":
            session_id = message.get("session_id")
            sessions[session_id] = {"addr": addr, "last_seq": 0}

            ack_msg = {
                "type": "INIT_ACK",
                "session_id": session_id,
                "status": "OK",
                "timestamp": int(time.time())
            }
            server_socket.sendto(json.dumps(ack_msg).encode(), addr)
            print(f"[Server] Sent INIT_ACK: {ack_msg} ({time.ctime(ack_msg['timestamp'])})")

        elif msg_type == "DATA":
            session_id = message.get("session_id")
            seq = message.get("seq")

            if session_id not in sessions:
                err_msg = {
                    "type": "ERROR",
                    "session_id": session_id,
                    "error": "Unknown session",
                    "timestamp": int(time.time())
                }
                server_socket.sendto(json.dumps(err_msg).encode(), addr)
                continue

            sessions[session_id]["last_seq"] = seq

            ack_msg = {
                "type": "DATA_ACK",
                "session_id": session_id,
                "seq": seq,
                "timestamp": int(time.time())
            }
            server_socket.sendto(json.dumps(ack_msg).encode(), addr)
            print(f"[Server] Sent DATA_ACK for seq={seq} ({time.ctime(ack_msg['timestamp'])})")

if __name__ == "__main__":
    main()
