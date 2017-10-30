import config
import threading
import time
import udt
import util


# Go-Back-N reliable transport protocol.
class GoBackN:

  # "msg_handler" is used to deliver messages to application layer
  def __init__(self, local_port, remote_port, msg_handler):
    self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
    self.msg_handler = msg_handler

    self.base = 1
    self.next_sequence_number = 1
    self.set_timer()

    # TODO: dont know if i need these yet
    #self.last_pkt_sent = b''
    #self.last_pkt_sent_data = None
    #self.sender_lock = threading.Lock()
    #self.sender_state = config.WAIT_FOR_APP_DATA
    #self.is_receiver = True
    # TODO: what data structure for my window? array? linked list? map?


  def set_timer(self):
    self.timer = threading.Timer((config.TIMEOUT_MSEC/1000.0), self._timeout)

  # "send" is called by application. Return true on success, false
  # otherwise.
  def send(self, msg):
    # TODO: this is only called by the sender
    # If next_seq_# < base + WINDOW_SIZE:
    #   sndpkt[next_seq_#] = make_packet(msg, DATA, next_seq_#)
    #   udt_send(sndpkt[next_seq#])
    #   if(base == next_seq_3) start_timer
    #   next_seq_#++
    # Else:
    #   refuse data # TODO: refuse data?? will the app just send it again?
    # TODO: do I need to spawn a thread here to wait for window space? I think so...

    # TODO: impl protocol to send packet from application layer.
    # call self.network_layer.send() to send to network layer.
    pass
    # TODO: needs to return True on success

  # "handler" to be called by network layer when packet is ready.
  def handle_arrival_msg(self):
    msg = self.network_layer.recv()
    # TODO: impl protocol to handle arrived packet from network layer.
    # call self.msg_handler() to deliver to application layer.
    pass

  # Cleanup resources.
  def shutdown(self):
    # TODO: cleanup anything else you may have when implementing this
    # class.
    if self.timer.is_alive(): self.timer.cancel()
    util.log("Connection shutting down...")
    self.network_layer.shutdown()


  def _timeout(self):
    self.set_timer()
    self.timer.start()
    # start the timer again
    # resend all packets from base -> nextseqnum-1
    # self.network_layer.send(all those packets)
    return