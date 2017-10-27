# Usage: python file_receiver.py [dummy|ss|gbn] [file_name]
import config
import functools
import os.path
import sys
import time
import util


def msg_handler(file_handle, msg):
  print("Received MSG of length" + str(len(msg)))
  file_handle.write(msg.decode("utf-8", "ignore"))


if __name__ == '__main__':
  if len(sys.argv) != 3:
    print('Usage: python file_receiver.py [dummy|ss|gbn] [file_name]')
    sys.exit(1)

  transport_layer = None
  transport_layer_name = sys.argv[1]
  file_name = sys.argv[2]
  assert os.path.exists(file_name)
  file_handle = None
  try:
    file_handle = open(file_name, 'w')
    transport_layer = util.get_transport_layer_by_name(
        transport_layer_name,
        config.RECEIVER_LISTEN_PORT,
        config.SENDER_LISTEN_PORT,
        functools.partial(msg_handler, file_handle))
    while True:
      time.sleep(1)
  finally:
    if file_handle:
      file_handle.close()
    if transport_layer:
      transport_layer.shutdown()
