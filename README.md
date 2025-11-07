IoT Telemetry Protocol (ITP) -Phase 1 Prototype.  
Computer Networking (CSE361)

The repository is the Phase 1 prototype of the IoT Telemetry Protocol (ITP), a simple UDP-based application-layer protocol that is based on application-level protocols and that is used to send sensor readings to a central collector as a result of IoT devices.

The project includes:
UDP client (simulator client Python)
One python UDP server (collector)
Mini-RFC (Sections 1-3)
The automated baseline test script.
Sample logs

# 1.0 Project Overview

The IoT Telemetry Protocol (ITP) is a lightweight protocol that is an application layer to do work in constrained IoT environments where:
Messages are small  
Latency must be low  
Overhead must be minimal  
UDP is preferred over TCP  

# Phase 1 illustrates the essences of message exchange:

INIT - INITACK  
   A client initiates a session by a send of an INIT message.

DATA - DATAACK  
   The client propagates telemetry measurements (e.g. temperature), sequentially numbered.

The server authenticates the sessions, records messages and sends back the acknowledgements.

# 2.0 MiniRFC

Message Encoding
Messages are all UTF-8 JSON objects, which are sent in single datagrams over UDP.

Common Fields
  Field          Description                            

  type         Type of a message (INIT, DATA, ACK, ERROR)  
  sessionid   Client generated session identifier.      
  timestamp Representation of the UNIX epoch seconds.                     

Additional Fields
  Message Type   Extra Fields                 

  DATA           seq, payload             
  INITACK       status                     
  DATA_ACK       seq                        
  ERROR          error (description)        

Transport
UDP  
Default port: 5005  
IPv4  
No retransmission  
None of the batching (introduced at subsequent stages)
