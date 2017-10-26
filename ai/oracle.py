"""
inference of network.
while True:
    addr, features = queue.get_all_or_a_batch()
    oracles = predict_fn(features)
    send_back(addr, oracles)
"""

import zmq
import msgpack
import msgpack_numpy
import Queue

msgpack_numpy.patch()


class Predictor(object):
    def __init__():
        self.cache = {}
        self.queue = Queue.Queue()

    def _buildsockets(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        self.socket.bind('ipc://./tmp/oracle')
        print("FINISH build socket")

    def _continuous_recv(self):
        while True:
            content = self.socket.recv()
            content = msgpack.loads(content)


if __name__ == "__main__":
    predictor = Predictor()
