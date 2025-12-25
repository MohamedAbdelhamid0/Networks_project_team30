#!/usr/bin/env python3


# da version el mafeho4 network_sim. da el mafrod yetsalem. el tany kona ben test be bs take care!!

import socket, struct, json, time, csv, datetime
from collections import defaultdict, deque
import pandas as pd

SERVER_IP = "0.0.0.0"
SERVER_PORT = 5005

# Header packing: !B H H d  -> 1 + 2 + 2 + 8 = 13 bytes.
HDR_FMT = "!B H H d"
HDR_LEN = struct.calcsize(HDR_FMT)

MSG_INIT = 0
MSG_DATA = 1
MSG_ACK  = 2
MSG_END  = 3
MSG_HEARTBEAT = 4


REORDER_BUFFER_SECONDS = 0.3 

PACKET_LOG = "packets_log.csv"
ANALYSIS_LOG = "packets_log_sorted_by_timestamp.csv"

# Global session state (for all connected devices)
sessions = defaultdict(lambda: {
    "addr": None,
    "received_seqs": set(),
    "last_seq": 0,
    "arrival_times": {},
    "recv_buffer": deque(),
    "last_hb": 0,
    "last_batch_size": 1 
})

ALL_PACKET_ROWS = [] 

def get_detailed_ts(t):
    return datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S.%f')

def unpack_header(raw):
    if len(raw) < HDR_LEN:
         raise ValueError("Packet too short for header")
    header = struct.unpack(HDR_FMT, raw[:HDR_LEN])
    header_byte, device_id, seq, timestamp = header
    version = (header_byte >> 4) & 0xF
    msgtype = header_byte & 0xF
    return version, msgtype, device_id, seq, timestamp

def pack_ack(version, device_id, ack_seq, msgtype):
    current_time = time.time()
    header_byte = ((version & 0xF) << 4) | (msgtype & 0xF)
    return struct.pack(HDR_FMT, header_byte, device_id & 0xFFFF, ack_seq & 0xFFFF, current_time)

def get_batch_gap_info(readings, expected_first_id):
    # cheks for gaps *inside* the batch payload itself
    if not readings:
        return False, []

    actual_ids = {r.get("reading_id") for r in readings if isinstance(r.get("reading_id"), int)}
    if not actual_ids:
        return False, []

    expected_ids = set(range(expected_first_id, expected_first_id + len(readings)))
    
    missing_ids_in_batch = list(expected_ids - actual_ids)
    
    if missing_ids_in_batch:
        return True, sorted(missing_ids_in_batch)
    
    return False, []

def write_packet_log_row(row):
    global ALL_PACKET_ROWS
    ALL_PACKET_ROWS.append(row)

def analyze_log_and_sort():
    
    if not ALL_PACKET_ROWS:
        print("No packets logged to analize.")
        return

    df = pd.DataFrame(ALL_PACKET_ROWS, columns=['device_id', 'seq', 'timestamp', 'arrival_time', 'duplicate_flag', 'gap_flag', 'payload_len'])
    
    # Convert timestamp columns to datetime objects
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S.%f')
    df['arrival_time'] = pd.to_datetime(df['arrival_time'], format='%Y-%m-%d %H:%M:%S.%f')
    
    # Sort by the client's timestamp
    df_sorted = df.sort_values(by='timestamp').reset_index(drop=True)
    
    # Calculate Network Delay (Latency).
    df_sorted['network_delay_s'] = (df_sorted['arrival_time'] - df_sorted['timestamp']).dt.total_seconds().round(6)
    
    # Save the sorted data to a new CSV file
    df_sorted.to_csv(ANALYSIS_LOG, index=False, date_format='%Y-%m-%d %H:%M:%S.%f')
    print(f"Analysis complete. Sorted packet log saved to {ANALYSIS_LOG}")

def run_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((SERVER_IP, SERVER_PORT))
    print(f"UDP server listening on {SERVER_IP}:{SERVER_PORT}")

    try:
        while True:
            raw, addr = sock.recvfrom(65535) 
            arrival_time = time.time()
            arrival_ts_str = get_detailed_ts(arrival_time)

            # Netem already handled the impairment. Direct processing.
            out_list = [(raw, addr)]
            
            for raw_pkt, pkt_addr in out_list:
                
                try:
                    version, msgtype, device_id, seq, ts = unpack_header(raw_pkt)
                    payload_len = len(raw_pkt) - HDR_LEN
                    ts_str = get_detailed_ts(ts)
                except struct.error:
                    print(f"[{arrival_ts_str}] [Server] Error unpacking header from {pkt_addr}. discarding.")
                    continue

                # Session Initialization/Lookup
                session = sessions[device_id]
                if session["addr"] is None:
                    session["addr"] = pkt_addr
                    print(f"[{arrival_ts_str}] [Server] New session started by device {device_id} at {pkt_addr}")

                # --- MESSAGE TYPE HANDLERS ---

                if msgtype == MSG_INIT:
                    # Clear state and confirm handshake (ACK)
                    sessions[device_id]["received_seqs"] = {0} 
                    sessions[device_id]["last_seq"] = 0
                    
                    ack = pack_ack(version, device_id, seq, MSG_ACK)
                    sock.sendto(ack, pkt_addr)
                    print(f"[{arrival_ts_str}] [Server] INIT from device {device_id} seq={seq}. ACK sent.")
                    continue

                if msgtype == MSG_HEARTBEAT:
                    # just update time and ACK
                    sessions[device_id]["last_hb"] = arrival_time
                    
                    ack = pack_ack(version, device_id, seq, MSG_ACK)
                    sock.sendto(ack, pkt_addr)
                    print(f"[{arrival_ts_str}] [Server] HEARTBEAT from device {device_id}. ACK sent.")
                    continue

                if msgtype == MSG_DATA:
                    
                    is_dup = seq in sessions[device_id]["received_seqs"]
                    packet_gap_flag = False
                    
                    # 1. Duplicate check and suppression
                    if is_dup:
                        # Log it as a duplicate, then ignore the payload.
                        row = [device_id, seq, ts, arrival_time, 1, 0, payload_len]
                        write_packet_log_row(row)
                        
                        print(f"[{arrival_ts_str}] [Server] Duplicate DATA from device {device_id} seq={seq}. Ignoring.")
                        ack = pack_ack(version, device_id, seq, MSG_ACK)
                        sock.sendto(ack, pkt_addr)
                        continue 
                    
                    # 2. Sequence Gap Detection 
                    expected_next_seq = sessions[device_id]["last_seq"] + sessions[device_id]["last_batch_size"]
                    
                    if seq > expected_next_seq:
                        packet_gap_flag = True
                    
                    # Update state
                    sessions[device_id]["received_seqs"].add(seq)
                    
                    # 3. Payload processing
                    try:
                        payload = raw_pkt[HDR_LEN:]
                        payload_obj = json.loads(payload.decode('utf-8'))
                        readings = payload_obj.get("batch", [])
                        batch_size = len(readings)
                        
                        # Internal Batch Gap Check 
                        batch_gap_info = get_batch_gap_info(readings, seq)
                        
                        sessions[device_id]["last_seq"] = max(sessions[device_id]["last_seq"], seq)
                        sessions[device_id]["last_batch_size"] = batch_size if batch_size > 0 else 1

                    except json.JSONDecodeError:
                        print(f"[{arrival_ts_str}] [Server] JSON decode fail from device {device_id} seq={seq}. Payload ignored.")
                        batch_size = 0
                        batch_gap_info = (False, [])
                        sessions[device_id]["last_batch_size"] = 1 

                    # Log the packet 
                    row = [device_id, seq, ts, arrival_time, int(is_dup), int(packet_gap_flag), payload_len]
                    write_packet_log_row(row) 

                    log_output = f"[{arrival_ts_str}] DATA RECEIVED :: DEVICE {device_id} :: SEQ {seq} :: BATCH {batch_size} :: SIZE {payload_len} :: CLIENT TS {ts_str}"
                    
                    if packet_gap_flag:
                        log_output += " :: MISSING PACKET BEFORE THIS"
                    if batch_gap_info[0]:
                        log_output += f" :: BATCH MISSING IDS: {', '.join(map(str, batch_gap_info[1]))}"
                    print(log_output)

                    ack = pack_ack(version, device_id, seq, MSG_ACK)
                    sock.sendto(ack, pkt_addr)
                    continue

                print(f"[{arrival_ts_str}] UNKOWN MESSAGE TYPE :: DEVICE {device_id} :: TYPE: {msgtype}")

    except KeyboardInterrupt:
        print("\nSHUTDOWN REQUESTED. PROCESSING LOGS...")
        analyze_log_and_sort()
    finally:
        sock.close()

if __name__ == "__main__":
    # Check pandas
    try:
        import pandas as pd
        run_server()
    except ImportError:
        print("Error: pandas library not found. Please install with 'pip install pandas' to enable analysis.")
