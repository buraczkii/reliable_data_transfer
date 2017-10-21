import dummy
import gbn
import ss


def get_transport_layer_by_name(name, local_port, remote_port, msg_handler):
  assert name == 'dummy' or name == 'ss' or name == 'gbn'
  if name == 'dummy':
    return dummy.DummyTransportLayer(local_port, remote_port, msg_handler)
  if name == 'ss':
    return ss.StopAndWait(local_port, remote_port, msg_handler)
  if name == 'gbn':
    return gbn.GoBackN(local_port, remote_port, msg_handler)
