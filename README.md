# IoT Telemetry Protocol (ITP) — Phase 1 Prototype  
Computer Networking (CSE361)

The present repository holds the Phase 1 prototype implementation of the IoT Telemetry Protocol (ITP), a lightweight UDP-based application-layer protocol that is used to send sensor readings of IoT-based devices to a central collector.

## 1.0 Project Overview

IoT Telemetry Protocol (ITP) is an application-layer protocol that is a bespoke, lightweight, and used in constrained internet-of-things (IoT) settings, in which the protocol:
--> Messages are small  
--> Latency must be low  
--> Overhead must be minimal  
--> UDP is preferred over TCP

 *Phase 1 illustrates the essence of the exchange of messages:* 

INIT - INITACK  
   The client initiates a session by giving an INIT message.

DATA - DATAACK  
   The client transmits telemetry measurements (e.g. temperature), and they have a sequence number.

The server authenticates messages, records messages and retrieves acknowledgments.
---

## 2.0 Protocol Summary (Mini-RFC Overview)

### Message Encoding
All messages are UTF-8 JSON objects transmitted in single UDP datagrams.

### Common Fields
Each field in the protocol has three fundamental fields:
--> type - This informs the server of the type of message. e.g. INIT, DATA, INITACK, DATAack or ERROR.
--> session-id - This is a special identifier that is selected by the client as it initiates the session.
--> timestamp - The time of the message generation time in the UNIX epoch seconds.

### Additional Fields
There are other fields that are added in some types of messages:
--> Messages of the DATA format contain two additional items:
   --> a sequence number called seq,
   --> and a payload
--> The INIT ACK messages have a status field which confirms that the server took the session.
--> The DATA_ACK messages contain the same seq number as the client sent and the client can therefore know which DATA message was acknowledged.
--> ERROR messages include an error field that is a brief description of the cause of the error (such as an invalid session ID).


# Transport
--> Transport Protocol: Obviously, we used UDP in our project  || Addressing: IPV4 || Default port for sending/receiving: 5005 

