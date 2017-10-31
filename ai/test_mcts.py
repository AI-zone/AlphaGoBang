from ai.mcts_policy import Tree, plot_pi, legal, move_state
from env.gobang import Game, axis, toind

import zmq
import msgpack
import msgpack_numpy
from env.gobang import show

msgpack_numpy.patch()


class Tester(object):
    def __init__(self):
        self.identity = '0-0'
        self._buildsockets()

    def _buildsockets(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.DEALER)
        self.socket.setsockopt_string(zmq.IDENTITY, self.identity)
        self.socket.connect('ipc://./tmp/oracle_recv.ipc')
        print("FINISH build socket")

    def send_batch(self, batch_data):
        batch_data = [(str(i[0]), str(i[1])) for i in batch_data]
        self.socket.send(msgpack.dumps((batch_data, self.identity)))

    def recv(self):
        content = self.socket.recv()
        content = msgpack.loads(content)
        return content


if __name__ == "__main__":
    tester = Tester()
    f = open('/data/gobang/warmup', 'r').readlines()
    import random
    for i in range(5):
        line = random.choice(f).split(',')
        show(int(line[0]), int(line[1]))
        print(axis(int(line[2])), line[2])
        tester.send_batch([(line[0], line[1])])
