# Reliable Data Transfer : Programming Assignment 3
## 'Stop and go' and 'Go back N' protocols for RDT
---
## Susanna Edens | October 30, 2017


#### Playing around with network layer parameters:
- error rate probability
- packet loss probability
- RTT
- How is protocol affected?

##### for both protocols:
- how does it handle timeout? duplicate data/ack? corrupted data?

- the pros/cons of each protocol.
- under what network behaviour/status would you choose this protocol over the other


### STOP AND GO
- the alg
- how implemented
- pros/cons (when you would want to use this protocol)

- when receiving corrupt data, SG does nothing. The FSM asks the receiver to resend
the last ack if the received data is corrupt. HOWEVER this will be ignored by the
sender (as it is assumed that the sender is not in a waiting for ack state) and
the timer for the sender will resend the data anyway


### GO BACK N
- the alg
- how implemented
- pros/cons


### Addt'l notes
- ...
