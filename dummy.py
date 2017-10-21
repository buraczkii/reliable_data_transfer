import udt


# A dummy transport layer to show how to interact with unreliable
# network layer. This dummny transport layer just send and recv
# messages from the underlining network layer without any check on
# loss or bit errors.
class DummyTransportLayer:
  # "msg_handler" is used to deliver messages to application layer
  # when it's ready.
  def __init__(self, local_port, remote_port, msg_handler):
    self.network_layer = udt.NetworkLayer(local_port, remote_port, self)
    self.msg_handler = msg_handler

  # "send" is called by application. Return true on success, false
  # otherwise.
  def send(self, msg):
    self.network_layer.send(msg)
    return True

  # "handler" to be called by network layer when packet is ready.
  def handle_arrival_msg(self):
    msg = self.network_layer.recv()
    self.msg_handler(msg)

  # Cleanup resources.
  def shutdown(self):
    self.network_layer.shutdown()
