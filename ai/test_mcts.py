from ai.mcts_policy import Tree, plot_pi, legal, move_state
from env.gobang import Game, axis, toind

import zmq
import msgpack
import msgpack_numpy
from blist import blist
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
    g = Game()
    g.add(7, 7)
    g.add(7, 9)
    g.add(11, 11)
    g.add(7, 8)
    g.add(9, 9)
    g.add(8, 9)
    g.add(6, 9)
    g.add(7, 6)
    for i in range(2):
        tester.send_batch([(g.black, g.white)] * 2)
    #content = tester.recv()
