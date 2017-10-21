import collections
import config
import random
import socket
import threading
import time


class NetworkLayer:
  def __init__(self, local_port, remote_port, transport_layer):
    # Port for recv and send packets.
    self.local_port = local_port
    self.remote_port = remote_port
    # Listening on local_port to recv packets.
    self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.s.bind(('localhost', local_port))
    # self.s.setblocking(False)
    self.s.settimeout(0.5)  # seconds.
    # Hold transport layer object for message demultiplexing.
    self.transport_layer = transport_layer
    # Buffer for holding messages to be delivered to transport layer.
    self.msg_buffer = collections.deque(maxlen=8)
    self.buffer_lock = threading.Lock()
    # Start reading network packet thread.
    self.stop_accept_pkt = False
    threading.Thread(target=self._packet_reader).start()


  def shutdown(self):
    self.stop_accept_pkt = True


  # msg should be of type bytes, not string.
  def send(self, msg):
    if random.random() < config.BIT_ERROR_PROB:
      msg = self._random_bit_error(msg)
    if random.random() < config.MSG_LOST_PROB:
      return
    time.sleep(config.RTT_MSEC / 2000.0)
    self.s.sendto(msg, ('localhost', self.remote_port))


  def recv(self):
    msg = ''
    with self.buffer_lock:
      if len(self.msg_buffer) > 0:
        msg = self.msg_buffer.popleft()
    return msg


  def _packet_reader(self):
    while not self.stop_accept_pkt:
      # If there is received msg, notify the transport layer instead
      # of blocking reading.
      has_msg = False
      with self.buffer_lock:
        if len(self.msg_buffer) > 0:
          has_msg = True
      if has_msg:
        self.transport_layer.handle_arrival_msg()
        continue
      try:
        msg, addr = self.s.recvfrom(config.MAX_SEGMENT_SIZE)
        with self.buffer_lock:
          if len(self.msg_buffer) < self.msg_buffer.maxlen:
            self.msg_buffer.append(msg)
      except socket.timeout:
        # If timeout happens, just continue.
        pass


  # Return a new msg with random bit errors.
  def _random_bit_error(self, msg):
    l = len(msg)
    byte_index = random.randrange(l)
    prefix = msg[:byte_index]
    suffix = msg[byte_index+1:]
    original_byte = msg[byte_index]
    changed_byte = bytes([original_byte ^ 255])
    return prefix + changed_byte + suffix
