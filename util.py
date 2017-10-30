import dummy
import gbn
import ss
import struct
import time

SIXTEEN_BIT_MASK = 0xffff

# A class to wrap various pieces of information included in a transport layer segment which includes
#  the type of message (ACK or DATA), the sequence number, the checksum value, and the payload. In
# addition, it contains a boolean flag indicating the presence of data corruption.
class RDTPacket:
  def __init__(self, msg_type, seq_num, checksum, payload, is_corrupt):
    self.msg_type = msg_type
    self.seq_num = seq_num
    self.checksum = checksum
    self.payload = payload
    self.is_corrupt = is_corrupt


def get_corrupt_packet_representation():
  return RDTPacket(None, None, None, None, True)


####################################################


def get_checksum(pkt):
  checksum = 0
  byte_list = list(pkt[i:i+2] for i in range(0, len(pkt), 2))
  for chunk in byte_list:
    num = struct.unpack('!H', chunk)[0] if len(chunk) == 2 else struct.unpack('!B', chunk)[0]
    checksum += num
  # fold the carry so the checksum is 16 bits long
  checksum = (checksum >> 16) + (checksum & SIXTEEN_BIT_MASK)
  return checksum ^ SIXTEEN_BIT_MASK   # get one's complement


def make_packet(msg, type, seq_num):
  bytelist = []
  bytelist.append(struct.pack('!H', type))     # HEADER 1: MESSAGE TYPE
  bytelist.append(struct.pack('!H', seq_num))  # HEADER 2: SEQUENCE NUMBER
  bytelist.append(struct.pack('!H', 0))        # HEADER 3: CHECKSUM (append 0 for now)
  bytelist.append(msg)                         # The payload

  checksum = get_checksum(b''.join(bytelist))
  checksum_bytes = struct.pack("!H", checksum)
  assert len(checksum_bytes) == 2

  bytelist[2] = checksum_bytes
  packet = b''.join(bytelist)
  return packet


def extract_data(msg):
  if len(msg) < 6 or not get_checksum(msg) == 0:
    return get_corrupt_packet_representation()
  headers = struct.unpack("!3H", msg[0:6])
  return RDTPacket(headers[0], headers[1], headers[2], msg[6:], False)


def pkt_to_string(pkt):
  type = "type: " + ("ACK" if pkt.msg_type == 2 else "DATA")
  seq_num = "seq#: " + str(pkt.seq_num)
  payload = ""
  if(pkt.payload):
    payload = ", payload: " + str(pkt.payload)[:20]
    if len(pkt.payload) > 20: payload += "..."
  return " [" + type + ", " + seq_num + payload + "]"


def get_transport_layer_by_name(name, local_port, remote_port, msg_handler):
  assert name == 'dummy' or name == 'ss' or name == 'gbn'
  if name == 'dummy':
    return dummy.DummyTransportLayer(local_port, remote_port, msg_handler)
  if name == 'ss':
    return ss.StopAndWait(local_port, remote_port, msg_handler)
  if name == 'gbn':
    return gbn.GoBackN(local_port, remote_port, msg_handler)


def now():
  return time.strftime("[%a %m-%d-%y %H:%M:%S] ")


def log(msg):
  print(now() + msg)
