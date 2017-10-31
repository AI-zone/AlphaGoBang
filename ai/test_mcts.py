from ai.mcts_policy import Tree, plot_pi, legal, move_state
from env.gobang import Game, axis, toind
import sys
import zmq
import msgpack
import msgpack_numpy
from env.gobang import show
from tqdm import tqdm
msgpack_numpy.patch()


class Tester(object):
    def __init__(self, sid, pid):
        self.identity = b'%d-%d' % (sid, pid)
        self.sid = sid
        self._buildsockets()

    def _buildsockets(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.IDENTITY, self.identity)
        self.socket.connect('ipc://./tmp/oracle_recv%d.ipc' % self.sid)
        print("FINISH build socket")

    def send_batch(self, batch_data):
        batch_data = [(str(i[0]), str(i[1])) for i in batch_data]
        self.socket.send(msgpack.dumps((batch_data, self.identity)))

    def recv(self):
        content = self.socket.recv()
        content = msgpack.loads(content)
        return content


if __name__ == "__main__":
    sid = int(sys.argv[1])
    pid = int(sys.argv[2])
    tester = Tester(sid, pid)
    f = open('/data/gobang/warmup', 'r').readlines()
    import random
    for i in tqdm(range(3000)):
        lines = random.sample(f, 256)
        tester.send_batch([(line.split(',')[0], line.split(',')[1])
                           for line in lines if len(line) > 10])
        content = tester.recv()
