# baseline_test.py: Automates the baseline local UDP test between client and server.
import subprocess
import time
import sys

def main():
    print("[Test] Starting baseline local test...\n")

    # --- Start the server subprocess (unbuffered output) ---
    server = subprocess.Popen(
        [sys.executable, "-u", "udp_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    time.sleep(1)  # Allow server to initialize

    # --- Start the client subprocess ---
    client = subprocess.Popen(
        [sys.executable, "udp_client.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    try:
        # Capture client output (wait until it finishes)
        client_out, _ = client.communicate(timeout=20)
    except subprocess.TimeoutExpired:
        client.kill()
        client_out, _ = client.communicate()
        print("[Test] Client timed out.")

    print("\n[Test] Client output:")
    print(client_out.strip())

    # --- Give the server time to process and respond ---
    time.sleep(1)
    server.terminate()

    try:
        server_out, _ = server.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        server.kill()
        server_out, _ = server.communicate()
        print("[Test] Server forced to stop after timeout.")

    print("\n[Test] Server output:")
    print(server_out.strip())

    print("\n[Test] Baseline scenario completed.")

if __name__ == "__main__":
    main()
