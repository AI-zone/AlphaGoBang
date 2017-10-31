# @Author: chenyu
# @Date:   20_Oct_2017
# @Email:  yu.chen@pku.edu.cn
# @Filename: server.py
# @Last modified by:   chenyu
# @Last modified time: 21_Oct_2017

import threading
import numpy as np
import zmq
import time
import msgpack
import msgpack_numpy
from env.gobang import Game
import config
msgpack_numpy.patch()


class Server(threading.Thread):
    """Server."""

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
        for _ in range(config.MODE):
            _addr, content = self.socket.recv_multipart()
            self.addr.append(_addr)
        print("FINISH build socket")

    def _send(self, end=None):
        if not end:
            self.socket.send_multipart([
                self.addr[(self.g.t + self.offset) % config.MODE],
                msgpack.dumps((self.g.t, str(self.g.black), str(self.g.white)))
            ])
        else:
            for i in range(config.MODE):
                self.socket.send_multipart([
                    self.addr[i],
                    msgpack.dumps((end, str(self.g.black), str(self.g.white)))
                ])

    def _recv(self):
        _addr, content = self.socket.recv_multipart()
        return msgpack.loads(content)

    def _new_game(self):
        self.g.newround()

    def _run_a_round(self):
        self.offset = np.random.randint(2)
        self._new_game()

        for _ in range(config.GAMELENGTH):
            self._send()
            x, y = self._recv()
            result = self.g.add(x, y)
            if result in 'BWJ':
                self._send(result)
                print('Finish a round', result)
                return
            elif result == 'F':
                print('##########')
        # special tag
        self._send('E')

    def run(self):
        np.random.seed()
        self._buildsocket()
        while True:
            self._run_a_round()
            self.g.show()
            # input("ENTER TO CONTINUE")


if __name__ == "__main__":
    f = open('/data/gobang/selfplay/' + str(int(time.time())), 'a')
    f.close()
    servers = [Server(sid) for sid in range(config.NUMPARALELL)]
    for s in servers:
        s.start()
