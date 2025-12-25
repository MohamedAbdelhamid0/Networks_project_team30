import os
import subprocess
import time
import sys
import signal

# --- CONFIGURATION ---
INTERFACE = "enp0s8" 
# ---

SERVER_SCRIPT = "udp_server.py"
PCAP_FILTER = "udp and port 5005"
SERVER_LOG_FILE = "server_log.txt"
PCAP_FILE = "trace.pcap"

# Mapping for file organization
SCENARIOS = {
    "1": "baseline",
    "2": "loss",
    "3": "delay"
}

def run_single_test(scenario_key, run_num):
    """
    Executes one full test cycle:
    1. Starts tcpdump for pcap capture.
    2. Starts the server and redirects its output to a temporary file.
    3. Waits for the user to run the client on Windows.
    4. Stops the server and capture processes.
    5. Organizes the output files.
    """
    
    scenario_name = SCENARIOS.get(scenario_key)
    if not scenario_name:
        print("Invalid scenario key.")
        return

    # 1. Setup Directories
    output_dir = os.path.join("raw_data", scenario_name)
    os.makedirs(output_dir, exist_ok=True)
    
    # Define temporary files (will be renamed later)
    temp_pcap_path = PCAP_FILE
    temp_server_log_path = SERVER_LOG_FILE
    temp_log_csv_path = "packets_log_sorted_by_timestamp.csv" # Saved by the server
    
    print(f"\n--- Starting {scenario_name.upper()} Run #{run_num} ---")
    print(f"[1] Starting tcpdump on interface {INTERFACE}...")
    
    # 2. Start tcpdump (Packet Capture)
    try:
        # Use subprocess.Popen for non-blocking start
        # NOTE: We need to use sudo for tcpdump. The user may be prompted for a password.
        tcpdump_command = ["sudo", "tcpdump", "-i", INTERFACE, "-w", temp_pcap_path, PCAP_FILTER]
        tcpdump_process = subprocess.Popen(tcpdump_command, preexec_fn=os.setsid, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"    tcpdump started (PID: {tcpdump_process.pid})")
    except FileNotFoundError:
        print("Error: tcpdump not found. Ensure it is installed and in your PATH.")
        return
    except Exception as e:
        print(f"Error starting tcpdump: {e}")
        return

    # 3. Start Python Server
    print(f"[2] Starting UDP server ({SERVER_SCRIPT})...")
    try:
        # Use a temporary file for the server's console output
        with open(temp_server_log_path, 'w') as log_file:
            # Use -u for unbuffered output
            server_command = ["python3", "-u", SERVER_SCRIPT]
            server_process = subprocess.Popen(server_command, stdout=log_file, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
        
        print(f"    Server started (PID: {server_process.pid}). Output logged to {temp_server_log_path}")
        time.sleep(2) # Give the server time to start up and bind the socket
        
    except FileNotFoundError:
        print(f"Error: Python script {SERVER_SCRIPT} not found.")
        # Attempt cleanup of tcpdump before returning
        os.killpg(os.getpgid(tcpdump_process.pid), signal.SIGTERM)
        return
    
    # 4. Wait for Client Test (Manual Step on Windows)
    print("\n" + "="*50)
    print(f"    !!! ACTION REQUIRED !!!")
    print(f"    1. CONFIGURE CLUMSY (Windows) for {scenario_name.upper()} test.")
    print(f"    2. RUN CLIENT: python udp_client.py (on Windows PC).")
    print(f"    3. Wait for client to finish (approx 20 seconds).")
    print("="*50 + "\n")
    
    input(">>> Press ENTER on THIS Linux terminal after the client finishes...")

    # 5. Stop Server Gracefully (SIGINT to save logs)
    print("\n[3] Stopping server gracefully (sending SIGINT)...")
    try:
        # Send SIGINT (Ctrl+C) to the server process to trigger log analysis/saving
        os.killpg(os.getpgid(server_process.pid), signal.SIGINT)
        server_process.wait(timeout=5) # Wait up to 5 seconds for it to save logs and exit
        print("    Server exited gracefully.")
    except (ProcessLookupError, subprocess.TimeoutExpired):
        print("Warning: Server did not exit gracefully. Forcing kill.")
        # If it timed out or process not found, force kill
        os.killpg(os.getpgid(server_process.pid), signal.SIGKILL)
        
    # 6. Stop tcpdump
    print("[4] Stopping tcpdump capture...")
    try:
        # Send SIGTERM to the tcpdump process
        os.killpg(os.getpgid(tcpdump_process.pid), signal.SIGTERM)
        tcpdump_process.wait(timeout=5)
        print("    tcpdump stopped.")
    except (ProcessLookupError, subprocess.TimeoutExpired):
        print("Warning: tcpdump did not exit gracefully. Forcing kill.")
        os.killpg(os.getpgid(tcpdump_process.pid), signal.SIGKILL)

    # 7. Organize and Rename Files
    print("[5] Organizing files...")
    run_label = f"{scenario_name}_run{run_num}"
    
    # Define final file paths
    final_pcap_path = os.path.join(output_dir, f"{run_label}_trace.pcap")
    final_server_log_path = os.path.join(output_dir, f"{run_label}_console_log.txt")
    final_csv_path = os.path.join(output_dir, f"{run_label}_packets_log.csv")
    
    # Move and rename temporary files
    try:
        os.rename(temp_pcap_path, final_pcap_path)
        os.rename(temp_server_log_path, final_server_log_path)
        os.rename(temp_log_csv_path, final_csv_path)
        print(f"    Files saved to {output_dir}/ with prefix {run_label}")
    except FileNotFoundError as e:
        print(f"Error: Required output file not found during rename: {e}")
        print("A run may need to be repeated.")

    print(f"\n--- {scenario_name.upper()} Run #{run_num} COMPLETE ---")


def main_menu():
    """Presents the user with a menu to select the test scenario."""
    while True:
        print("\n" + "="*30)
        print("UDP Experiment Automation Script")
        print("="*30)
        print("1. Baseline (No Clumsy)")
        print("2. Loss (5% Drop)")
        print("3. Delay (100ms Lag)")
        print("Q. Quit")
        
        choice = input("Select scenario (1/2/3/Q): ").strip().upper()
        
        if choice == 'Q':
            print("Exiting script.")
            break
        
        if choice in SCENARIOS:
            while True:
                run_num = input(f"Enter Run Number (1-5) for {SCENARIOS[choice]}: ").strip()
                if run_num.isdigit() and 1 <= int(run_num) <= 5:
                    break
                else:
                    print("Please enter a number between 1 and 5.")
            
            run_single_test(choice, run_num)
        else:
            print("Invalid choice. Please select 1, 2, 3, or Q.")


if __name__ == "__main__":
    # Check if we are running with elevated privileges (needed for tcpdump)
    # This check is basic and mainly informative
    if os.geteuid() != 0:
        print("INFO: You may need to run this script with 'sudo python3 run_experiments.py' ")
        print("      or add your user to the 'wireshark' group for tcpdump to work.")
        print("-" * 30)

    # The original script would handle this, but for Python:
    # Check for pandas on the server, as the server script requires it for log analysis.
    try:
        import pandas as pd
    except ImportError:
        print("CRITICAL ERROR: pandas library not found.")
        print("The server script requires 'pandas' to sort the logs before saving.")
        print("Please install it on your Linux VM: 'pip install pandas' or 'pip3 install pandas'")
        sys.exit(1)
        
    main_menu()