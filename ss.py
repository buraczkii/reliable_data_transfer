import config
import udt
import util
import threading
import time


# Stop-And-Wait reliable transport protocol.
class StopAndWait:
  # "msg_handler" is used to deliver messages to application layer
  # when it's ready.
  def __init__(self, local_port, remote_port, msg_handler):
    self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
    self.msg_handler = msg_handler

    #TODO: consolidate. only need one field for seq num and last packet
    # Sender information to keep track of
    self.sender_lock = threading.Lock()
    self.sender_seq_num = 0
    self.sender_last_pkt = b''
    self.sender_waiting_state = config.WAIT_FOR_APP_DATA
    self.set_timer()

    # Receiver information to keep track of
    self.receiver_seq_num = 0
    self.receiver_last_pkt = b''
    self.is_receiver = True


  def set_timer(self):
    self.timer = threading.Timer((config.TIMEOUT_MSEC/1000.0), self._timeout)


  # "send" is called by application. Return true on success, false otherwise.
  def send(self, msg):
    self.is_receiver = False
    print(util.sender_log_header() + "Called by app to send following message: <" + str(msg) + ">")
    threading.Thread(target=self.send_helper(msg))
    return True


  def send_helper(self ,msg):
    print(util.sender_log_header() + "Waiting to send this message: <" + str(msg) + ">")
    while self.sender_waiting_state == config.WAIT_FOR_ACK_MSG:
      print("sleeping in while loop")
      time.sleep(1)

    self.sender_lock.acquire()
    packet = util.make_packet(msg, config.MSG_TYPE_DATA, self.sender_seq_num)
    self.network_layer.send(packet)
    print(util.sender_log_header() + "Acquired the lock. Sending this packet: <" + str(packet) + ">")
    self.sender_last_pkt = packet
    self.sender_waiting_state = config.WAIT_FOR_ACK_MSG
    if self.timer.is_alive(): self.timer.cancel()
    self.set_timer()
    self.timer.start()
    self.sender_lock.release()

    return


  # "handler" to be called by network layer when packet is ready. from BELOW
  def handle_arrival_msg(self):
    msg = self.network_layer.recv()
    #print("handling arrival message: "+ str(msg))
    msg_data = util.extract_data(msg)

    if(msg_data.is_corrupt):
      if(self.is_receiver):
        print(util.receiver_log_header()
              + "Resending ACK because message received was corrupt. ACK: <"
              + str(self.receiver_last_pkt) + ">")
        self.network_layer.send(self.receiver_last_pkt)
      return

    # If ACK message, assume its for sender
    if msg_data.msg_type == config.MSG_TYPE_ACK:
      if self.sender_waiting_state == config.WAIT_FOR_ACK_MSG \
              and msg_data.seq_num == self.sender_seq_num:
        print(util.sender_log_header()
              + "Received the expected ACK message of sequence # "
              + str(msg_data.seq_num) + ".")
        self.sender_lock.acquire()
        self.timer.cancel()
        self.sender_seq_num = not (self.sender_seq_num)  # flip the sequence number
        self.sender_waiting_state = config.WAIT_FOR_APP_DATA
        self.sender_lock.release()
    # If DATA message, assume its for receiver
    else:
      assert msg_data.msg_type == config.MSG_TYPE_DATA
      print(util.receiver_log_header() + "Recieved the following message: <" + str(msg) + ">.")
      if msg_data.seq_num == self.receiver_seq_num:
        print(util.receiver_log_header()
              + "Received the expected DATA message of sequence # "
              + str(msg_data.seq_num) + ".")
        self.msg_handler(msg_data.payload)
        ack_pkt = util.make_packet(b'', config.MSG_TYPE_ACK, self.receiver_seq_num)
        self.network_layer.send(ack_pkt)
        self.receiver_last_pkt = ack_pkt
        self.receiver_seq_num = not (self.receiver_seq_num) # flip the sequence number
      else:
        print(util.receiver_log_header()
              + "Received duplicate DATA message. Resending ACK message with sequence # "
              + str(int(self.receiver_seq_num)) + ".")
        self.network_layer.send(self.receiver_last_pkt)
    return


  # Cleanup resources.
  def shutdown(self):
    header = util.receiver_log_header() if self.is_receiver else util.sender_log_header()
    print(header + "Success! Shutting down connection now.")
    if self.timer.is_alive(): self.timer.cancel()
    # TODO: cleanup anything else you may have when implementing this class.
    # TODO: cleanup locks, timers, stored last packets
    self.network_layer.shutdown()


  def _timeout(self):
    print(util.sender_log_header() + "Timeout! Resending the last packet: <" + str(self.sender_last_pkt) + ">.")
    self.sender_lock.acquire()
    self.network_layer.send(self.sender_last_pkt)
    self.set_timer()
    self.timer.start()
    self.sender_lock.release()
    return
