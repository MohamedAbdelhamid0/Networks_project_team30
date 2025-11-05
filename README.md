# Telemetry Prototype (Phase 1 deliverable)

Files:
- udp_server.py: UDP server listening on 127.0.0.1:5005
- udp_client.py: UDP client that sends INIT + 5 DATA messages
- baseline_test.py: launches server and client and collects logs

Run manually:
1. Open two terminals.
2. Run: python udp_server.py
3. In the other: python udp_client.py

Or run automated baseline:
python baseline_test.py

Requires: Python 3.x (no external packages)

# telemetry_project

Minimal instructions:

1. Create a GitHub repository (or use an existing one).
   - Using GitHub CLI:
     gh repo create <owner>/<repo> --public --source=. --remote=origin --push
   - Or create repo on github.com and copy the remote URL.

2. Or run the helper script:
   - Open PowerShell in this project root and run:
     .\scripts\push_to_github.ps1 -RemoteUrl "<REMOTE_URL>" -CommitMessage "Initial commit"

Replace <REMOTE_URL> with your HTTPS or SSH remote URL.
