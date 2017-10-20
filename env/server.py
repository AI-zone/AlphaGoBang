# @Author: chenyu
# @Date:   20_Oct_2017
# @Email:  yu.chen@pku.edu.cn
# @Filename: server.py
# @Last modified by:   chenyu
# @Last modified time: 21_Oct_2017

import threading
import numpy as np
import zmq
import msgpack
import msgpack_numpy
from env.gobang import Game
msgpack_numpy.patch()


class Server(threading.Thread):
    """你来写"""

    def __init__(self, sid):
        super().__init__()
        self.g = Game()
        self.players_color = {}
        self.sid = sid
        self.offset = None

    def _buildsocket(self):
        context = zmq.Context()
        socket = context.socket(zmq.ROUTER)
        socket.bind('ipc://./tmp/server' + str(self.sid))
        self.socket = socket
        self.addr = []
        _addr, content = self.socket.recv_multipart()
        self.addr.append(_addr)
        _addr, content = self.socket.recv_multipart()
        self.addr.append(_addr)

    def _send(self, end=None):
        if not end:
            self.socket.send_multipart([
                self.addr[(self.g.t + self.offset) % 2],
                msgpack.dumps((self.g.t, str(self.g.black), str(self.g.white)))
            ])
        else:
            self.socket.send_multipart([
                self.addr[0],
                msgpack.dumps((-1, str(self.g.black), str(self.g.white)))
            ])
            self.socket.send_multipart([
                self.addr[1],
                msgpack.dumps((-1, str(self.g.black), str(self.g.white)))
            ])

    def _recv(self):
        _addr, content = self.socket.recv_multipart()
        return msgpack.loads(content)

    def _new_game(self):
        self.g.newround()

    def _run_a_round(self):
        self.offset = np.random.randint(2)
        self._new_game()

        while True:
            self._send()
            x, y = self._recv()
            result = self.g.add(x, y)
            if result in 'BW':
                self._send(result)
                return
            elif result == 'F':
                print('##########')

    def run(self):
        np.random.seed()
        self._buildsocket()
        for _ in range(100):
            self._run_a_round()
            print('Finish a round')
            self.g.show()


if __name__ == "__main__":
    server = Server(0)
    server.start()
