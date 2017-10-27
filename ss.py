import config
import struct
import threading
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
    self.slock = threading.Lock()
    # TODO: need to start a timer in here

  # "send" is called by application. Return true on success, false
  # otherwise.
  def send(self, msg):
    # TODO: impl protocol to send packet from application layer.
    packet = self.make_packet(self, msg, config.MSG_TYPE_DATA) # TODO: will it always be a msg type DATA here?
    self.network_layer.send(packet) # to send data to network layer
    # 3. start the timer
    pass

  # "handler" to be called by network layer when packet is ready.
  # from BELOW
  def handle_arrival_msg(self):
    msg = self.network_layer.recv()
    # TODO: impl protocol to handle arrived packet from network layer.
    # call self.msg_handler() to deliver to application layer.

    # are you an ACK of the right sequence number? stop timer

    #

    ## CASES
    # Sender 1: waiting for ACK 0 from receiver
    

    pass

  # Cleanup resources.
  def shutdown(self):
    # TODO: cleanup anything else you may have when implementing this
    # class.
    self.network_layer.shutdown()


  def make_packet(self, msg, type):
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



