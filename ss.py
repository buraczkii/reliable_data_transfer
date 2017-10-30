import config
import struct
import udt
import util


# Stop-And-Wait reliable transport protocol.
class StopAndWait:
  # "msg_handler" is used to deliver messages to application layer
  # when it's ready.
  def __init__(self, local_port, remote_port, msg_handler):
    self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
    self.msg_handler = msg_handler
    self.sequence_num = 0 # this is the sequence number flag
    #self.slock = threading.Lock()
    # TODO: need to start a timer in here for the sender & respond appropriately to timeout
    # TODO: need to figure out a way to handle a timers starts and stops
    # TODO: figure out how to create separate instances of this class so its threadsafe
    # TODO: SENDER: keep track of state (0 or 1) && store the last packet sent
    # TODO: SENDER: keep track of if waiting for call from above or if waiting for ACK
    # TODO: RECEIVER: keep track of state (0 or 1) && store the last packet sent

  # "send" is called by application. Return true on success, false
  # otherwise.
  # TODO: AKA rdt_send
  def send(self, msg):
    # TODO: this will only ever be called by the sender to resend msg type DATA packets
    # Create a packet with the current sender state as the sequence number
    # Send the packet to the network
    # Start the timer
    packet = self.make_packet(self, msg, config.MSG_TYPE_DATA)
    self.network_layer.send(packet)
    pass

  # "handler" to be called by network layer when packet is ready.
  # from BELOW
  # TODO: AKA rdt_rcv
  def handle_arrival_msg(self):
    # TODO: impl protocol to handle arrived packet from network layer.
    msg = self.network_layer.recv()

    # TODO: if the packet received is ACK, this regards the sender
    # CASE1: waiting for call from above => do nothing (either state 0 or 1)
    # CASE2: waiting for ack:
    #   (A) data is corrupt or has sequence number that does not match the state => do nothing
    #   (B) data is not corrupt and seq number matches state => stop the timer

    # TODO: if the packet received is DATA, this regards the receiver
    # CASE1: data is corrupt or has seq number that does not match state => resend last packet sent (ACK)
    # CASE2: data is not corrupt and matches seq number =>
    #   - extract the data from the packet
    #   - deliver the data to the application (by calling msg_handler)
    #   - create an ACK packet with the current state as the sequence number
    #   - send the ACK packet to the network layer (udt_send)
    # CASE2:
    # CASE4: In state 0, waiting for call from above => do nothing


    self.msg_handler(msg)
    pass


  # Cleanup resources.
  def shutdown(self):
    # TODO: cleanup anything else you may have when implementing this
    # class.
    self.network_layer.shutdown()


  def timeout(self):
    # TODO: implement this function
    # TODO: this function needs to be called when the timer times out
    # State 1: means you are waiting for Ack 1. Send DATA1 again
    # State 0: means you are waiting for Ack 0. Send DATA0 again
    # Call udt_send(last_packet_sent)
    # start_timer
    return


  def make_packet(self, msg, type):
    # TODO: test that this does what its supposed to do. tests?
    bytelist = []
    # HEADER 1: MESSAGE TYPE # TODO: remove the assert statements once im sure this works
    bytelist.append(struct.pack('H', type)[0])
    assert len(bytelist) == 2

    # HEADER 2: SEQUENCE NUMBER
    bytelist.append(struct.pack('H', self.sequence_num)[0])
    assert len(bytelist) == 4

    # HEADER 3: CHECKSUM
    checksum = util.get_checksum(msg) # TODO: need to get checksum for headers & message
    bytelist.append(struct.pack('H', checksum)[0])
    assert len(bytelist) == 6

    # TODO: is this in bytes? need to make sure appending the correct form for the data
    bytelist.append(msg)
    return b''.join(bytelist)



