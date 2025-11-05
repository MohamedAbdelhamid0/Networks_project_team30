import socket
import json
import time
import os  # NEW: used to give each client a unique session ID

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5005

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(3)

    # --- Each client uses its process ID as a unique session ID ---
    session_id = os.getpid()

    # --- Send INIT ---
    init_time = int(time.time())
    init_msg = {
        "type": "INIT",
        "session_id": session_id,
        "timestamp": init_time
    }
    client_socket.sendto(json.dumps(init_msg).encode(), (SERVER_IP, SERVER_PORT))
    print(f"[Client {session_id}] Sent INIT: {init_msg} ({time.ctime(init_time)})")

    try:
        data, addr = client_socket.recvfrom(1024)
        response = json.loads(data.decode())
        print(f"[Client {session_id}] Received: {response}")
        if 'timestamp' in response:
            print(f"   ↳ Timestamp: {response['timestamp']} ({time.ctime(response['timestamp'])})")
    except socket.timeout:
        print(f"[Client {session_id}] No INIT_ACK received.")
        return

    # --- Send DATA messages ---
    for seq in range(1, 4):
        data_time = int(time.time())
        data_msg = {
            "type": "DATA",
            "session_id": session_id,
            "seq": seq,
            "payload": {"value": seq * 10},
            "timestamp": data_time
        }
        client_socket.sendto(json.dumps(data_msg).encode(), (SERVER_IP, SERVER_PORT))
        print(f"[Client {session_id}] Sent DATA seq={seq}, payload={data_msg['payload']} ({time.ctime(data_time)})")

        try:
            data, addr = client_socket.recvfrom(1024)
            response = json.loads(data.decode())
            print(f"[Client {session_id}] Received: {response}")
            if 'timestamp' in response:
                print(f"   ↳ Timestamp: {response['timestamp']} ({time.ctime(response['timestamp'])})")
        except socket.timeout:
            print(f"[Client {session_id}] No ACK for DATA seq={seq}")

    client_socket.close()

if __name__ == "__main__":
    main()
