# IoT Telemetry Protocol (ITP) — Phase 1 Prototype
### Computer Networking (CSE361)

The present repository holds the Phase 1 prototype implementation of the **IoT Telemetry Protocol (ITP)**, a lightweight UDP-based application-layer protocol that is used to send sensor readings of IoT-based devices to a central collector. 

This system is designed for reproducible testing and robust analysis of UDP reliability under various network conditions.

---

## 1.0 Project Overview

IoT Telemetry Protocol (ITP) is an application-layer protocol that is bespoke, lightweight, and used in constrained internet-of-things (IoT) settings, in which the protocol focuses on:

* **Small Messages:** Minimal packet size to save bandwidth.
* **Low Latency:** Optimized for real-time response.
* **Minimal Overhead:** Reduced header data compared to TCP.
* **UDP Transport:** Preferred over TCP for speed and simplicity.



### Core Message Flow
* **INIT - INITACK:** The client initiates a session by giving an `INIT` message. The server responds with an `INITACK` to confirm readiness.
* **DATA - DATAACK:** The client transmits telemetry measurements (e.g. temperature) with a sequence number. The server confirms receipt with a `DATAACK`.

The server authenticates messages, records data, and manages acknowledgments.

---

## 2.0 Protocol Summary (Mini-RFC Overview)

### Message Encoding
All messages are **UTF-8 JSON objects** transmitted in single UDP datagrams.

### Header Format
The system uses a custom binary header (13 bytes) followed by the JSON payload.
**Format:** `!B H H d` (Big-endian)

| Offset | Field | Type | Size | Description |
| :--- | :--- | :--- | :--- | :--- |
| 0 | Version & Type | `!B` | 1 Byte | Upper 4 bits: Version / Lower 4 bits: Type |
| 1 | Device ID | `!H` | 2 Bytes | Unsigned short (Unique identifier) |
| 3 | Sequence No | `!H` | 2 Bytes | Unsigned short (Increments per packet) |
| 5 | Timestamp | `!d` | 8 Bytes | Double (Seconds since epoch) |

### JSON Field Definitions
* **Common Fields:** `type` (Message category), `session-id` (Unique client ID), and `timestamp`.
* **DATA:** Contains `seq` (sequence number) and `payload`.
* **INITACK:** Includes a `status` field confirming session acceptance.
* **DATAACK:** Includes the matching `seq` number for acknowledgment.
* **ERROR:** Includes an `error` field describing the cause (e.g., "Invalid Session ID").

---

## 3.0 Transport Specification
* **Transport Protocol:** UDP (User Datagram Protocol)
* **Addressing:** IPv4
* **Default Port:** 5005

---

## 4.0 Experiment Scenarios
Each scenario is run multiple times for statistical reliability. Results are analyzed for loss rate, gap rate, and latency.

* **Baseline:** No network impairment.
* **Loss:** Simulated packet loss.
* **Delay:** Simulated network delay.

---

## 5.0 File Structure
```text
.
├── analyze_results.py      # Statistical analysis script
├── run_experiments.py      # Automation for scenarios
├── udp_client.py           # Client-side telemetry source
├── udp_server.py           # Server-side collector
├── raw_data/               # Directory for log files
│   ├── baseline/
│   ├── loss/
│   └── delay/
└── final_analysis_summary.csv


6.0 Quick Start
