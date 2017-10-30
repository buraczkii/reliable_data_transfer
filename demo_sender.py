# Usage: python demo_sender.py [dummy|ss|gbn]
import config
import sys
import time
import util


if __name__ == '__main__':
  if len(sys.argv) != 2:
    print('Usage: python demo_sender.py [dummy|ss|gbn]')
    sys.exit(1)

  transport_layer = None
  name = sys.argv[1]
  start_time = time.time()
  try:
    transport_layer = util.get_transport_layer_by_name(
        name, config.SENDER_LISTEN_PORT,
        config.RECEIVER_LISTEN_PORT, None)
    for i in range(20):
      msg = 'MSG:' + str(i)
      print(msg)
      while not transport_layer.send(str.encode(msg)):
        pass
  finally:
    if transport_layer:
      transport_layer.shutdown()
    end_time = time.time()
    print('Time used [secs]:', end_time - start_time)
