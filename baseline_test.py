# baseline_test.py: Run baseline test with multiple concurrent clients and one server
import subprocess
import time
import threading

def run_client(index, results):
    """Run one client and store its output in the shared results dict."""
    client = subprocess.Popen(
        ['python', '-u', 'udp_client.py'],  # "-u" for unbuffered output
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    try:
        client_out, _ = client.communicate(timeout=20)
        results[index] = client_out.strip()
    except subprocess.TimeoutExpired:
        results[index] = f'[Error] Client {index+1} timed out.'
        client.kill()
    except Exception as e:
        results[index] = f'[Error] Client {index+1} failed: {e}'

def main():
    num_clients = 3  # Number of concurrent clients to spawn

    print('[Test] Starting server...')
    server = subprocess.Popen(
        ['python', '-u', 'udp_server.py'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )

    time.sleep(1.5)  # Give the server a bit longer to start

    print(f'[Test] Launching {num_clients} concurrent clients...\n')
    results = {}
    threads = []

    # Launch all clients concurrently using threads
    for i in range(num_clients):
        t = threading.Thread(target=run_client, args=(i, results))
        t.start()
        threads.append(t)

    # Wait for all clients to finish
    for t in threads:
        t.join()

    # Give server time to log any final messages
    time.sleep(1)
    server.terminate()
    try:
        server_out, _ = server.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        server.kill()
        server_out, _ = server.communicate()

    # Print collected outputs
    print('\n==================== CLIENT OUTPUTS ====================')
    for i in range(num_clients):
        print(f'\n[Test] Client {i+1} output:')
        print(results.get(i, '[No output]'))

    print('\n==================== SERVER OUTPUT ====================')
    print(server_out.strip())
    print('\n[Test] Concurrent multi-client baseline scenario completed.')

if __name__ == '__main__':
    main()
