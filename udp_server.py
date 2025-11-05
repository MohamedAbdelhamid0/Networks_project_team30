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

        # Extract fields for better readability
        msg_type = message.get("type")
        session_id = message.get("session_id", "unknown")
        ts = message.get("timestamp", int(time.time()))
        time_str = time.ctime(ts)

        print(f"[Server] Received from {addr} | session_id={session_id} | type={msg_type} | time={time_str}")

        if msg_type == "INIT":
            sessions[session_id] = {"addr": addr, "last_seq": 0}

            ack_msg = {
                "type": "INIT_ACK",
                "session_id": session_id,
                "status": "OK",
                "timestamp": int(time.time())
            }
            server_socket.sendto(json.dumps(ack_msg).encode(), addr)
            print(f"[Server] Sent INIT_ACK → session_id={session_id} ({time.ctime(ack_msg['timestamp'])})")

        elif msg_type == "DATA":
            seq = message.get("seq")
            payload = message.get("payload")

            if session_id not in sessions:
                err_msg = {
                    "type": "ERROR",
                    "session_id": session_id,
                    "error": "Unknown session",
                    "timestamp": int(time.time())
                }
                server_socket.sendto(json.dumps(err_msg).encode(), addr)
                print(f"[Server] ERROR: Unknown session_id={session_id}")
                continue

            sessions[session_id]["last_seq"] = seq

            ack_msg = {
                "type": "DATA_ACK",
                "session_id": session_id,
                "seq": seq,
                "timestamp": int(time.time())
            }
            server_socket.sendto(json.dumps(ack_msg).encode(), addr)
            print(f"[Server] Sent DATA_ACK → session_id={session_id}, seq={seq} ({time.ctime(ack_msg['timestamp'])})")

if __name__ == "__main__":
    main()
