import dummy
import gbn
import ss
import struct

MAX = 1 << 16
ALL_ONES_16_BIT = 65535

def add_16_bit_nums(n1,n2):
  res = n1 + n2
  if res.bit_length() <= 16: return res
  return (res + 1) % MAX # wrap the carry when necessary

# TODO: Assert that this function works as expected
def get_checksum(pkt):
  checksum = 0
  bytes = pkt.encode()
  byte_list = list(bytes[i:i+2] for i in range(0, len(bytes), 2))

  for chunk in byte_list:
    if len(chunk) ==1:
      num = struct.unpack('B', chunk)[0]
    else:
      num = struct.unpack('H', chunk)[0]
    checksum = add_16_bit_nums(checksum, num)

  return checksum ^ 65535   # get one's complement


def get_transport_layer_by_name(name, local_port, remote_port, msg_handler):
  assert name == 'dummy' or name == 'ss' or name == 'gbn'
  if name == 'dummy':
    return dummy.DummyTransportLayer(local_port, remote_port, msg_handler)
  if name == 'ss':
    return ss.StopAndWait(local_port, remote_port, msg_handler)
  if name == 'gbn':
    return gbn.GoBackN(local_port, remote_port, msg_handler)



# res = add_16_bit_nums(int('1010001111101001',2), int('1000000110110101',2))
# print(res)
# print(bin(res))
# check = get_checksum("hbiqwefhwisuhjuqw3ueioj32reuhiwjk3ewisuhjkeqwdsuihjkewfgrvd9ougk3rqwesdy8oihljwreds")
# print(check)
# print(bin(check))
#
# print(bin(check ^ 65535))
