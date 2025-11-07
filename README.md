# IoT Telemetry Protocol (ITP) — Phase 1 Prototype  
Computer Networking (CSE361)

This repository contains the Phase 1 prototype implementation of the IoT Telemetry Protocol (ITP), a lightweight UDP-based application-layer protocol designed for transmitting sensor readings from IoT devices to a central collector.

The project includes:
- A Python UDP client (sensor simulator)
- A Python UDP server (collector)
- Mini-RFC (Sections 1–3)
- Automated baseline test script
- Sample logs

---

## 🚀 Project Overview

The IoT Telemetry Protocol (ITP) is a custom, lightweight application-layer protocol designed for constrained IoT environments where:
- Messages are small  
- Latency must be low  
- Overhead must be minimal  
- UDP is preferred over TCP  

Phase 1 demonstrates the core message exchange:

1. **INIT → INIT_ACK**  
   The client starts a session by sending an INIT message.

2. **DATA → DATA_ACK**  
   The client sends telemetry readings (e.g., temperature), each with a sequence number.

The server validates sessions, logs messages, and responds with acknowledgments.

---

## 📡 Protocol Summary (Mini-RFC Overview)

### **Message Encoding**
All messages are UTF-8 JSON objects transmitted in single UDP datagrams.

### **Common Fields**
| Field        | Description                           |
|--------------|---------------------------------------|
| `type`       | Message type (INIT, DATA, ACK, ERROR) |
| `session_id` | Client-assigned session identifier     |
| `timestamp`  | UNIX epoch seconds                    |

### **Additional Fields**
| Message Type | Extra Fields                |
|--------------|-----------------------------|
| DATA         | `seq`, `payload`            |
| INIT_ACK     | `status`                    |
| DATA_ACK     | `seq`                       |
| ERROR        | `error` (description)       |

### **Transport**
- UDP  
- Default port: **5005**  
- IPv4  
- No retransmission  
- No batching yet (added in later phases)

---

## 🗂 Repository Structure

