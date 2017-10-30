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
        self.runner_id = b'basic'

    def _buildsockets(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.ROUTER)
        self.socket.bind('ipc://./tmp/oracle_recv.ipc')
        print("FINISH build socket")

    def send(self, mine, yours):
        print(mine, yours)
        self.socket.send_multipart([
            self.runner_id,
            msgpack.dumps((str(mine), str(yours), self.identity))
        ])

    def recv(self):
        content = self.socket.recv()
        content = msgpack.loads(content)
        return content


if __name__ == "__main__":
    tester = Tester()
    g = Game()
    g.add(7, 7)
    g.add(7, 8)
    tester.send(g.black, g.white)
    content = tester.recv()
