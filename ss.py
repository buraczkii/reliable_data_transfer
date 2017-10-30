import config
import udt
import util
from threading import Timer


# Stop-And-Wait reliable transport protocol.
class StopAndWait:
  # "msg_handler" is used to deliver messages to application layer
  # when it's ready.
  def __init__(self, local_port, remote_port, msg_handler):
    self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
    self.msg_handler = msg_handler
    self.sequence_num = 0 # this is the sequence number flag
    #self.slock = threading.Lock() # TODO: figure out if you need a lock for anything
    self.timer = Timer(config.TIMEOUT_MSEC, self._timeout) # creating a timer thats ready to go
    # TODO: figure out how to create separate instances of this class so its threadsafe
    # threading.Thread(target=self._packet_reader).start() # from udt class

    # TODO: SENDER: keep track of seq# (0 or 1) && last packet sent && if waiting for call from above or for ACK
    self.sender_seq_num = 0 # this also represents part of the state
    self.sender_last_pkt = ""
    self.sender_waiting_for = config.MSG_TYPE_ACK # this may be converted into a lock

    # TODO: RECEIVER: keep track of state (0 or 1) && store the last packet sent
    self.receiver_seq_num = 0
    self.receiver_last_pkt = ""

  # "send" is called by application. Return true on success, false otherwise.
  def send(self, msg):
    # TODO: can this be called while waiting for the last ACK? need a way to wait here if the timer is still going
    # TODO: need to lock here? put a lock on sending until the ack has been received
    # TODO: this will only ever be called by the sender to resend msg type DATA packets
    # Create a packet with the current sender state as the sequence number
    packet = util.make_packet(msg, config.MSG_TYPE_DATA, self.sender_seq_num)
    self.network_layer.send(packet)
    self.sender_last_pkt = packet # store the last packet sent
    self.sender_waiting_for = config.MSG_TYPE_ACK
    self.timer.start()


  # "handler" to be called by network layer when packet is ready.
  # from BELOW
  def handle_arrival_msg(self):
    msg = self.network_layer.recv()
    msg_data = util.extract_data(msg)

    # TODO: if the packet received is ACK, this regards the sender
    # CASE1: waiting for call from above => do nothing (either state 0 or 1)
    if(self.sender_waiting_for == config.MSG_TYPE_DATA):
      pass
    # CASE2: waiting for ack:
    if (self.sender_waiting_for == config.MSG_TYPE_ACK):
      #(A) data is corrupt or has sequence number that does not match the state => do nothing
      if(is_corrupt(msg) or not(get_seq_num(msg) == self.sender_seq_num)):
        pass
      #(B) data is not corrupt and seq number matches state => stop the timer
      else:
        self.timer.cancel()
        self.sender_seq_num = not(self.sender_seq_num) # flip the state
        self.sender_waiting_for = config.MSG_TYPE_DATA # you should always be waiting for DATA when you get here


    # TODO: if the packet received is DATA, this regards the receiver
    # CASE1: data is corrupt or has seq number that does not match state => resend last packet sent (ACK)
    if(is_corrupt(msg) or not(get_seq_num(msg) == self.receiver_seq_num)):
      self.network_layer.send(self.receiver_last_pkt)
    # CASE2: data is not corrupt and matches seq number =>
    else:
      #extract the data from the packet
      data = util.extract_data(msg)
      #deliver the data to the application (by calling msg_handler)
      self.msg_handler(data)
      #create an ACK packet with the current state as the sequence number
      ack_pkt = util.make_packet("", config.MSG_TYPE_ACK, self.receiver_seq_num)
      #send the ACK packet to the network layer (udt_send)
      self.network_layer.send(ack_pkt)
      self.receiver_last_pkt = ack_pkt

  # Cleanup resources.
  def shutdown(self):
    # TODO: cleanup anything else you may have when implementing this class.
    # TODO: cleanup locks, timers, stored last packets
    self.network_layer.shutdown()


  def _timeout(self):
    # TODO: implement this function. only ever timeout when waiting for ACK in sender state
    self.network_layer.send(self.sender_last_pkt)
    self.timer = Timer(config.TIMEOUT_MSEC, self._timeout())
    self.timer.start()
    return



