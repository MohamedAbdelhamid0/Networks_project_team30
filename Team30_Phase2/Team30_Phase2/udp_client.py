

import socket, struct, time, json, os, random
import datetime 

#8ayaro el IP lama tego te3mlo run. el IP ykoon nafs el 3la linux lama tekteb ifconfig


SERVER_IP = "192.168.1.10"
SERVER_PORT = 5005

# geda3an eftekro 3ayzeen n5aly el batch size ykoon input m4 fixed kda
# mmkn bardo nbos 3la ba2et el 7agat n5aleha input zy el number of messages aw kda
# hearbeat 5aly 4 w 5las w el ack_timeout bardo sebo zy ma howa.


HDR_FMT = "!B H H d"
HDR_LEN = struct.calcsize(HDR_FMT)


MSG_INIT = 0
MSG_DATA = 1
MSG_ACK  = 2
MSG_END  = 3
MSG_HEARTBEAT = 4


ACK_TIMEOUT = 3
MAX_RETRIES = 0
BASE_BACKOFF = 2
NUM_MESSAGES = 70
BATCH_SIZE = 1
HEARTBEAT_INTERVAL = 3


def send_best_effort(sock, packed_msg):
    try:
        sock.sendto(packed_msg, (SERVER_IP, SERVER_PORT))
        return True
    except Exception:
        return False


def pack_header(version, msgtype, device_id, seq, timestamp):
    header_byte = ((version & 0xF) << 4) | (msgtype & 0xF)
    return struct.pack(HDR_FMT, header_byte, device_id & 0xFFFF, seq & 0xFFFF, timestamp)

def unpack_header(raw):
    header = struct.unpack(HDR_FMT, raw[:HDR_LEN])
    header_byte, device_id, seq, timestamp = header
    version = (header_byte >> 4) & 0xF
    msgtype = header_byte & 0xF
    return version, msgtype, device_id, seq, timestamp

def get_detailed_ts(t):
    # keep the time format
    return datetime.datetime.fromtimestamp(t).strftime('%H:%M:%S.%f')

# For INIT only
def send_and_wait_ack(sock, packed_msg, expect_seq=None, expect_type=None, timeout=ACK_TIMEOUT):
    tries = 0
    while tries <= MAX_RETRIES:
        try:
            sock.sendto(packed_msg, (SERVER_IP, SERVER_PORT))
            sock.settimeout(timeout * (2 ** tries))
            data, _ = sock.recvfrom(4096)
            
            if len(data) < HDR_LEN:
                tries += 1
                continue
            
            v, t, did, seq_r, ts = unpack_header(data)
            if expect_type is not None and t != expect_type:
                tries += 1
                continue
            if expect_seq is not None and seq_r != expect_seq:
                tries += 1
                continue
            
            payload_bytes = data[HDR_LEN:]
            payload = None
            if payload_bytes:
                try:
                    payload = json.loads(payload_bytes.decode())
                except Exception:
                    payload = None
            return True, (v, t, did, seq_r, ts, payload)
        except socket.timeout:
            tries += 1
            if tries > MAX_RETRIES:
                return False, None
            backoff = BASE_BACKOFF * (2 ** (tries - 1)) * (0.8 + 0.4 * random.random())
            time.sleep(backoff)
        except Exception:
            return False, None
    return False, None

def main():
    device_id = os.getpid() & 0xFFFF
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    version = 1

    ts = time.time() 
    init_hdr = pack_header(version, MSG_INIT, device_id, 0, ts)
    init_payload = json.dumps({
    "proto": "AUDP-X",
    "version": 1,
    "info": "init"
    }).encode()

    init_packet = init_hdr + init_payload
    ok, resp = send_and_wait_ack(sock, init_packet, expect_type=MSG_ACK)
    
    if not ok:
        print(f"[{get_detailed_ts(time.time())}] FAILED INITIALIZE :: DEVICE {device_id} :: NO ACK. EXITING NOW.")
        return
        
    print(f"[{get_detailed_ts(time.time())}] SUCCESS HANDSHAKE :: DEVICE {device_id} :: ACK RECIEVED. RESPONSE {resp}")

    seq = 1
    last_heartbeat_time = time.time() 

    while seq <= NUM_MESSAGES:
        current_time = time.time()

        if current_time - last_heartbeat_time >= HEARTBEAT_INTERVAL:
            ts_str = get_detailed_ts(current_time)
            print(f"[{ts_str}] HEARTBEAT SENT :: DEVICE {device_id}")

            hb_hdr = pack_header(version, MSG_HEARTBEAT, device_id, 0, current_time)
            hb_packet = hb_hdr + b''
            send_best_effort(sock, hb_packet) 
            last_heartbeat_time = current_time
        

        readings = []
        for b in range(BATCH_SIZE):
            reading = {
                "reading_id": seq + b,
                "value": round(random.uniform(20.0, 30.0), 2),
                "unit": "C"
            }
            readings.append(reading)
        payload_obj = {
            "batch": readings
        }
        payload_bytes = json.dumps(payload_obj).encode()
        
        hdr = pack_header(version, MSG_DATA, device_id, seq, time.time())
        packet = hdr + payload_bytes

        ts_str = get_detailed_ts(time.time())
        
        if send_best_effort(sock, packet):
            print(f"[{ts_str}] DATA SENT OK :: DEVICE {device_id} :: SEQ {seq}")
            seq += BATCH_SIZE
        else:
            print(f"[{ts_str}] DATA SEND FAIL :: DEVICE {device_id} :: SEQ {seq} :: LOCAL SOCKET ERROR")
            seq += BATCH_SIZE
        
        time.sleep(1)

    end_hdr = pack_header(version, MSG_END, device_id, 0, time.time())
    end_packet = end_hdr + b''
    send_best_effort(sock, end_packet)
    sock.close()

if __name__ == "__main__":
    main()