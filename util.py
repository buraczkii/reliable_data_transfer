import config
import dummy
import gbn
import ss
import struct

SIXTEEN_BIT_MASK = 0xffff

# A class to wrap various pieces of information included in a data packet which includes the
# type of message (ACK or DATA), the sequence number, the checksum value, and the payload. In
# addition, it contains a boolean flag indicating bit corruption.
class RDTPacket:
  def __init__(self, msg_type=None, seq_num=None, checksum=None, payload=None, is_corrupt=True):
    self.msg_type = msg_type
    self.seq_num = seq_num
    self.checksum = checksum
    self.payload = payload
    self.is_corrupt = is_corrupt

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
  bytelist.append(struct.pack('!H', type))      # HEADER 1: MESSAGE TYPE
  bytelist.append(struct.pack('!H', seq_num))   # HEADER 2: SEQUENCE NUMBER
  bytelist.append(struct.pack('!H', 0))         # HEADER 3: CHECKSUM (append 0 for now)
  bytelist.append(msg.encode())                 # The payload # TODO: will the message be given as string or bytes object?

  checksum = get_checksum(b''.join(bytelist))
  checksum_bytes = struct.pack("!H", checksum)
  assert len(checksum_bytes) == 2

  bytelist[2] = checksum_bytes   # substitute checksum field with calculated checksum
  packet = b''.join(bytelist)
  return packet


# TODO: check that this works
def extract_data(msg):
  assert len(msg) >= 6
  # TODO: if during extraction, the packet is found to be corrupt, return the packet below
  corrupt_packet = RDTPacket() # TODO: try to put whatever data you have in there

  # TODO: given a full packet, extract the payload from the message. Return as RDTPacket object
  #packet = RDTPacket(msg_type, seq_num, checksum, payload, False)
  #1. calculate the checksum
  #2. compare the checksum to the 5-6bytes of the packet and see if they match
  #3. iterate through the message: the first 3 2-byte chunks are the headers. the rest is the
  # payload.
  # assert that msg is at least 6 bytes
  return corrupt_packet


def get_transport_layer_by_name(name, local_port, remote_port, msg_handler):
  assert name == 'dummy' or name == 'ss' or name == 'gbn'
  if name == 'dummy':
    return dummy.DummyTransportLayer(local_port, remote_port, msg_handler)
  if name == 'ss':
    return ss.StopAndWait(local_port, remote_port, msg_handler)
  if name == 'gbn':
    return gbn.GoBackN(local_port, remote_port, msg_handler)



# s = '4500003044224000800600008c7c19acae241e2b'
# bs = bytearray.fromhex(s)
# c = get_checksum(bs)
# print(c)