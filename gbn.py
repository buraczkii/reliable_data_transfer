import config
import threading
import time
import udt
import util


# Go-Back-N reliable transport protocol.
class GoBackN:

  # "msg_handler" is used to deliver messages to application layer
  def __init__(self, local_port, remote_port, msg_handler):
    util.log("Starting up `Go Back N` protocol ... ")
    self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
    self.msg_handler = msg_handler

    # sender stuff
    self.sender_base = 0
    self.next_sequence_number = 0
    self.set_timer()
    self.window = [b'']*config.WINDOW_SIZE

    # receiver stuff
    self.expected_sequence_number = 0
    self.receiver_last_ack = util.make_packet(b'', config.MSG_TYPE_ACK, 0)
    self.is_receiver = True

    self.sender_lock = threading.Lock()


  def set_timer(self):
    self.timer = threading.Timer((config.TIMEOUT_MSEC/1000.0), self._timeout)


  # "send" is called by application. Return true on success, false otherwise.
  def send(self, msg):
    self.is_receiver = False
    if self.next_sequence_number < (self.sender_base + config.WINDOW_SIZE): #TODO: -1 here?
      threading.Thread(target=self.send_helper(msg))
      return True
    else:
      print("data rejected")
      time.sleep(1) # TODO: give gbn a little time before the next request
      return False


  # Helper fn for thread to send the next packet
  def send_helper(self ,msg):
    print("inside send helper with msg: " + str(msg))
    self.sender_lock.acquire()
    packet = util.make_packet(msg, config.MSG_TYPE_DATA, self.next_sequence_number)
    packet_data = util.extract_data(packet)
    self.window[self.next_sequence_number%config.WINDOW_SIZE] = packet
    util.log("Sending data: " + util.pkt_to_string(packet_data))
    self.network_layer.send(packet)
    if self.sender_base == self.next_sequence_number:
      if self.timer.is_alive(): self.timer.cancel()
      self.set_timer()
      self.timer.start()
    self.next_sequence_number += 1
    self.sender_lock.release()
    return


  # "handler" to be called by network layer when packet is ready.
  def handle_arrival_msg(self):
    msg = self.network_layer.recv()
    msg_data = util.extract_data(msg)

    if(msg_data.is_corrupt):
      if(self.is_receiver):
        # Let the server timeout and resend the data if the first packet was corrupted
        if self.expected_sequence_number == 0: return
        ack_pkt = util.make_packet(b'', config.MSG_TYPE_ACK, self.expected_sequence_number-1)
        self.network_layer.send(ack_pkt)
        util.log("Received corrupt data. Resending ACK: " + util.pkt_to_string(util.extract_data(ack_pkt)))
        # TODO: maybe we can make a call to receiver_last_ack
      return

    # If ACK message, assume its for sender
    if msg_data.msg_type == config.MSG_TYPE_ACK:
      #util.log("Received ACK: " + util.pkt_to_string(msg_data))
      self.sender_lock.acquire()
      self.sender_base = msg_data.seq_num + 1 # TODO: why this? => Because seq num indicates successful transmission until this point
      if(self.sender_base == self.next_sequence_number):
        util.log("Received ACK with seq # matching the end of the window: " + util.pkt_to_string(msg_data) + ". Cancelling timer.")
        self.timer.cancel()
      else:
        util.log("Received ACK: " + util.pkt_to_string(msg_data) + ". There are messages in-flight. Restarting the timer.")
        if self.timer.is_alive(): self.timer.cancel()
        self.set_timer()
        self.timer.start()
      self.sender_lock.release()

    # If DATA message, assume its for receiver
    else:
      assert msg_data.msg_type == config.MSG_TYPE_DATA
      util.log("Received DATA: " + util.pkt_to_string(msg_data))
      if msg_data.seq_num == self.expected_sequence_number:
        self.msg_handler(msg_data.payload)
        ack_pkt = util.make_packet(b'', config.MSG_TYPE_ACK, self.expected_sequence_number)
        self.network_layer.send(ack_pkt)
        self.receiver_last_ack = ack_pkt
        self.expected_sequence_number += 1
        util.log("Sent ACK: " + util.pkt_to_string(util.extract_data(ack_pkt)))
      else:
        if self.expected_sequence_number == 0: return # No previous ack to send
        util.log("DATA message had unexpected sequence #" + str(int(msg_data.seq_num)) + ". Resending ACK message with sequence # "
                 + str(int(self.expected_sequence_number-1)) + ".") # TODO: revamp this log
        # TODO: is the receiver last ack going to be the expected sequence number? or one behind?
        ack_pkt = util.make_packet(b'', config.MSG_TYPE_ACK, (self.expected_sequence_number-1)) #TODO: i feel like this should be -1
        self.network_layer.send(ack_pkt)
        print("expected seq #=" + str(self.expected_sequence_number) + ". receiver_last_ack = " + str(self.receiver_last_ack))
        #self.network_layer.send(self.receiver_last_ack)
    return

  # Cleanup resources.
  def shutdown(self):
    if not self.is_receiver: self._wait_for_last_ACK()
    if self.timer.is_alive(): self.timer.cancel()
    util.log("Connection shutting down...")
    self.network_layer.shutdown()


  def _wait_for_last_ACK(self):
    print("Waiting for last ack. SenderBase#: " + str(self.sender_base) + ". NextSeq#: " + str(self.next_sequence_number-1) + ".")
    while self.sender_base < self.next_sequence_number-1:
      util.log("Waiting for last ACK from receiver with sequence # " + str(int(self.next_sequence_number)) + ".")
      time.sleep(1)

  def _timeout(self):
    util.log("Timeout! Resending all packets in window. Resending packets with seq #s "
             + str(self.sender_base) + "-" + str(self.next_sequence_number-1) +".")
    self.sender_lock.acquire()
    if self.timer.is_alive(): self.timer.cancel()
    self.set_timer()
    for i in range(self.sender_base,self.next_sequence_number):
      pkt = self.window[(i%config.WINDOW_SIZE)]
      self.network_layer.send(pkt)
      util.log("Resending packet: " + str(pkt)) # TODO revamp this log
    self.timer.start()
    self.sender_lock.release()
    return