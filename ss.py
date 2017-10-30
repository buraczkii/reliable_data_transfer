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
    self.sender_seq_num = 0
    self.sender_last_pkt = None
    self.sender_waiting_state = config.WAITING_FOR_APP_DATA # this may be converted into a lock

    # TODO: RECEIVER: keep track of state (0 or 1) && store the last packet sent
    self.receiver_seq_num = 0
    self.receiver_last_pkt = None

  # "send" is called by application. Return true on success, false otherwise.
  def send(self, msg):
    # TODO: can this be called while waiting for the last ACK? need a way to wait here if the timer is still going
    # TODO: need to lock here? put a lock on sending until the ack has been received
    # TODO: this will only ever be called by the sender to resend msg type DATA packets
    # Create a packet with the current sender state as the sequence number
    packet = util.make_packet(msg, config.MSG_TYPE_DATA, self.sender_seq_num)
    self.network_layer.send(packet)
    self.sender_last_pkt = packet # store the last packet sent
    self.sender_waiting_state = config.WAITING_FOR_ACK_MSG
    self.timer.start()


  # "handler" to be called by network layer when packet is ready. from BELOW
  def handle_arrival_msg(self):
    msg = self.network_layer.recv()
    msg_data = util.extract_data(msg)

    if(msg_data.is_corrupt):
      return

    # If ACK message, assume its for sender
    if msg_data.msg_type == config.MSG_TYPE_ACK:
      if self.sender_waiting_state == config.WAITING_FOR_ACK_MSG and msg_data.seq_num == self.sender_seq_num:
        self.timer.cancel()
        self.sender_seq_num = not (self.sender_seq_num)  # flip the sequence number
        self.sender_waiting_state = config.WAITING_FOR_APP_DATA
      return

    # If DATA message, assume its for receiver
    if msg_data.msg_type == config.MSG_TYPE_DATA:
      if msg_data.seq_num == self.receiver_seq_num:
        self.msg_handler(msg_data.payload)
        ack_pkt = util.make_packet("", config.MSG_TYPE_ACK, self.receiver_seq_num)
        self.network_layer.send(ack_pkt)
        self.receiver_last_pkt = ack_pkt
      else:
        self.network_layer.send(self.receiver_last_pkt) # resend last packet


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



