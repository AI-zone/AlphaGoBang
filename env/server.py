"""Server."""
# pylint: disable-msg=C0103
# pylint: disable-msg=E1101
# pylint: disable-msg=E0632

import threading
import numpy as np
import zmq
import msgpack
import msgpack_numpy
import config
from env.gobang import Game
from pprint import pprint
msgpack_numpy.patch()


class Server(threading.Thread):
    """Server."""

    def __init__(self, server_id, player1_id, player2_id):
        super().__init__()
        self.g = [Game() for i in range(config.GAMEPARALELL)]
        self.server_id = server_id
        seats = [player1_id, player2_id]
        self.seats = [[
            bytes('%s-%d' % (seats[i % 2], i), 'utf8'),
            bytes('%s-%d' % (seats[1 - i % 2], i), 'utf8')
        ] for i in range(config.GAMEPARALELL)]
        self.socket = None
        self.statistics = {
            player1_id: {k: 0
                         for k in 'BWJE'},
            player2_id: {k: 0
                         for k in 'BWJE'},
        }

    def _buildsocket(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.ROUTER)
        self.socket.bind('ipc://./tmp/server_%s' % self.server_id)
        for _ in range(2 * config.GAMEPARALELL):
            self._recv()
        print("%s FINISH build socket" % self.server_id)

    def _send_state(self, gid, result):
        """
            state:  t(or BWJE), black, white
        """
        pid = self.g[gid].t % 2
        if result == 'P':
            state = (self.g[gid].t, str(self.g[gid].black), str(
                self.g[gid].white))
            self.socket.send_multipart(
                [self.seats[gid][pid],
                 msgpack.dumps(state)])
        elif result in 'BWJE':
            state = (result, str(self.g[gid].black), str(self.g[gid].white))
            self.socket.send_multipart(
                [self.seats[gid][0], msgpack.dumps(state)])
            self.socket.send_multipart(
                [self.seats[gid][1], msgpack.dumps(state)])
            player = '-'.join(self.seats[gid][1
                                              - pid].decode().split('-')[:-1])
            self.statistics[player][result] += 1
            self._new_game(gid)
            self._send_state(gid, 'P')
            if gid == 0:
                pprint(self.statistics)
        else:
            raise RuntimeError("Invalid result %s" % result)

    def _recv(self):
        _, content = self.socket.recv_multipart()
        return msgpack.loads(content)

    def _new_game(self, gid):
        self.seats[gid] = self.seats[gid][::-1]
        self.g[gid].newround()

    def _run_infinite_round(self):
        for gid in range(config.GAMEPARALELL):
            self._new_game(gid)
            self._send_state(gid, 'P')

        while True:
            x, y, gid = self._recv()
            result = self.g[gid].add(x, y)
            if self.g[gid].t > config.GAMELENGTH:
                result = 'E'
            self._send_state(gid, result)

    def run(self):
        np.random.seed()
        self._buildsocket()
        self._run_infinite_round()


if __name__ == "__main__":
    pass
