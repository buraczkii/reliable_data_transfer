## Reliable Data Transfer : 'Stop and go' and 'Go back N' protocols
#### Susanna Edens | October 30, 2017


##### Playing around with network layer parameters:
- error rate probability
- packet loss probability
- RTT
- How is protocol affected?


##### `STOP AND GO` Protocol
THE ALGORITHM: the sender and receiver are both sending one message at a time. The sender sends a piece of data and waits for an acknowledgement from the receiver that the data was received successfully before sending the next piece of data.

Both the sender and receiver code are contained within the `ss.py` file. In order to distinguish between sender and receiver actions, the following observations are made:
- Messages with type `ACK` will only be received by the sender and sent by the receiver
- Messages with type `DATA` will only be received by the receiver and send by the sender
- The method `send()` will only be called for the sender

In a world where the underlying network has reliable data transfer properties, the sender and receiver will take turns, sending messages and acks to each other alternatively until all the data has been transmitted. However, that is not the case. Here are the possible scenarios that may occur and how I handled them:

**Special cases for the receiver**
  1. _Packet received is corrupt:_ When the packet received is corrupt, we cannot tell what the sequence number is or if it is duplicate data. Resend the last ACK. The sender will ignore ACKs with sequence numbers that do not match the current sequence number. The sender will timeout eventually and resend the last data packet it sent.
  1. _Packet received is a duplicate:_ This occurs when the sender times out due to either receiving corrupt ACKs, duplicate ACKs, or no ACKs at all. Resend the last ACK. Sender will eventually resend the next DATA packet.

**Special cases for the sender**
  1. _ACK received is corrupt:_ Do nothing. The timer will eventually go off, resending the last DATA packet. This will trigger the receiver to send another ACK packet with that sequence number. If we resent the last data packet every time we received a corrupt ACK, we would be flooding the channel with duplicate messages.
  1. _Timeout:_ When there is a timeout, this indicates that the sender did not receive the ACK it was waiting for. Resend the last data packet sent and restart the timer.
  1. _`Send` calls from above when waiting for ACKs:_ In order to handle this, I spawned a thread for each call made to `send()`. The thread waits for the sender state to switch to `WAIT_FOR_APP_DATA`, grabs the lock, sends the data, and restarts the timer.
  1. _Waiting for the last ack:_ There is a case where the sender may send the final message and since `send()` returns True on success, the sender may close the connection if not careful. The last message may be corrupt or dropped by the network so the sender must wait to receive the ACK from the receiver indicating successful transfer. The method to sit and wait for this is called in the `shutdown()` process.

**Advantages:**
- Stop and wait requires minimal state/memory. It only needs to hold a couple flags to record state, the last packet sent, a timer, and a lock.
- In a very unreliable network, stop and wait may reduce the number of messages in the channel since it individually asserts each message is successfully received before sending the next one.

**Disadvantages:**
- This is a slow, serial algorithm. If you want to send large pieces of data, this protocol will take a long time.
- Stop and wait has very low throughput. It takes 1RTT in between each message sending in the best case. In the worst case where there is corruption or data lost, it will be at least a couple RTTs before the subsequent message is sent.


##### `GO BACK N` Protocol
- the alg
- how implemented
- pros/cons

- how does it handle timeout? duplicate data/ack? corrupted data?
- under what network behaviour/status would you choose this protocol over the other


##### Addt'l notes
- ...
