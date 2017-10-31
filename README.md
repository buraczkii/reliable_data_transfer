# Reliable Data Transfer : 'Stop and go' and 'Go back N' protocols
#### Susanna Edens | October 30, 2017

### `STOP AND GO` Protocol
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

_Advantages:_
- Stop and wait requires minimal state/memory. It only needs to hold a couple flags to record state, the last packet sent, a timer, and a lock.
- In a very unreliable network, stop and wait may reduce the number of messages in the channel since it individually asserts each message is successfully received before sending the next one.
- In a network with very small propagation delay and small RTT, this algorithm will transmit the data quickly while minimizing the number of packets in the channel to do it.

_Disadvantages:_
- This is a slow, serial algorithm. If you want to send large pieces of data, this protocol will take a long time simply due to the RTT between each send.
- Stop and wait has very low throughput. It takes 1RTT in between each message sending in the best case. In the worst case where there is corruption or data lost, it will be at least a couple RTTs before the subsequent message is sent.
- If the propagation delay on the network is large, the RTT will be large and this will have a direct negative impact on speed/efficiency.


### `GO BACK N` Protocol
THE ALGORITHM: the sender has a sliding window buffer where N is both the number of packets that it can hold in its buffer and the number of data packets (more specifically, sequence numbers) that can be in-flight from the sender. The receiver expects packets to come in order and not corrupted. If so, it will send ACKs for each successful message. If not, it sends ACKs for the last successfully received message. If the sender times out, it will send all of the packets that are in its sliding window.

Both the sender and receiver code are contained within the `gbn.py` file. The same assumptions about data made in **STOP AND GO** were made here.

What happens when packets aren't received as expected?

**Special cases for the receiver**
  1. _Packet received is corrupt:_ When the packet received is corrupt, we cannot reliably say anything about its contents. Resend the last ACK sent, indicating the sequence number of the last DATA packet that was received successfully. If an ACK has not yet been sent, do nothing and wait for server to time out.
  1. _Packet received is out of order/does not match the expected sequence number:_  This could mean the packet is a duplicate or the packet that was expected was either corrupt or dropped, resulting in a stream of packets that are out of order. Resend the last ACK and wait for the server to timeout and resend the messages.

**Special cases for the sender**
  1. _ACK received is corrupt:_ Do nothing. The timer will eventually go off, resending the messages that have not yet been ACK-ed.
  1. _Timeout:_ When there is a timeout, this indicates that the sender did not receive ACKs for some number of messages in the current window. It resends all of those messages and restarts the timer.
  1. _Multithreaded `Send` calls_: I spawned a thread to handle sending app data. It waits to grab the lock, sends the data, and restarts the timer if the base is equal to the next sequence number (indicating messages in-flight). Lastly, it increments the `next_sequence_number`.
  1. _Waiting for the last ack:_ If the sender finishes sending its messages, there can be up to N messages still in flight without corresponding ACKs. For this reason, before the sender gets to shutdown, it will wait until its `base_number` has caught up with its `next_sequence_number`, indicating those messages have been ACK-ed.
  1. _No space in the window for more data:_ When a call comes from above wishing to send more data, if there is no room in the window, the sender will reject the data by returning False, indicating that the app should try again to send the same data. `gbn` sleeps for 1 second before returning false, just to give a little time for the possibility of window space becoming available next call.


_Advantages_
- Under good network conditions (low propagation delay), GBN can take better advantage of throughput by sending multiple messages without having to wait for ACKs. This would help in cases of large files.
- A given ACK can acknowledge multiple frames since the sequence number in an ACK indicates that all packets until that sequence number have been received successfully.

_Disadvantages_
- Depending on the window size, the buffer may take up a lot of space.
- Depending on the window size, corrupted packets may result in a large amount of duplicate messages sent. For example, if the window size is 100 and the sender sends 100 windows and all of them are received without error _except the first_, all of the packets will be resent.
- If the network is not the most stable or RTT is high, this protocol will flood the channels with duplicate messages due to timeout. Every time the server times out, it will resend all of the messages in its window. If the timeout is too fast, the receiver may have already sent ACKS for all of the messages but did not reach the sender in time. If the RTT is too high compared to the timeout, its possible that the receiver may still be processing the messages while the sender sends a duplicate batch.


### Calculating the checksum
I chose to implement the checksum algorithm the way its implemented in actual protocols instead of the simplified version. I find bit manipulation cool and I find the fact that _the checksum of a message containing the ones complement of the checksum of its data will equal 0 if not corrupt_ fascinating. The basic steps are as follows:
- Break the data into chunks of 16 bits and add them altogether
- Carry the overflow if the sum is now greater than 16 bits
- Take the ones complement of the checksum and return this value

**How to detect corruption**

When calculating the checksum for a newly created packet, the value for the checksum was 0. The ones complement of the checksum is then put into the checksum field. Upon packet arrival, take the checksum and if the checksum is 0, you can be relatively sure that no bit corruption occurred. You can only be relatively sure because reordering 16-bit chunks in your message can result in the same checksum if you split the chunks the same way. However, in a network where no malicious activity is assumed, bit corruption will typically be random and will be caught by using the checksum.

([Checksum reference](http://www.roman10.net/2011/11/27/how-to-calculate-iptcpudp-checksumpart-1-theory/))


### Playing around with network layer parameters:
```bash
    values (BIT_ERROR_PROB, MSG_LOST_PROB, RTT)
```

How are the protocols affected by different network conditions? (using `demo_receiver` and `_sender`). I ran the demo for each set of network parameters for each protocol 3 times. I averaged the time from those 3 data points. I took the sample of the median time to calculate how many messages were sent and how many timeouts occurred.


|                                   | Stop and Wait     | Go Back N         |
| -------------                     |:-------------:    |:-----             |
| Fake Network (0.01, 0.01, 100ms)  | Avg(3.17s) 21msgs | Avg(2.22s) 26msgs |
| Standard (0.1, 0.1, 100ms)        | Avg(5.2s) 29msgs  | Avg(4.8s) 98msgs |
| High corruption (0.3, 0.1, 100ms) | Avg(7.96s) 40msgs | Avg(5.19s) 104msgs |
| High drop rate (0.1, 0.3, 100ms)  | Avg(7.1s) 87msgs | Avg(7.99s) 159msgs |
| Higher RTT (0.1, 0.1, 150)          | Avg(6s) 28msgs | Avg(6.44s) 85msgs |