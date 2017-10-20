# @Author: chenyu
# @Date:   20_Oct_2017
# @Email:  yu.chen@pku.edu.cn
# @Filename: server.py
# @Last modified by:   chenyu
# @Last modified time: 20_Oct_2017

import threading
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
        self.turn = None
        self.players_color = {}
        self.sid = sid

    def _buildsocket(self):
        context = zmq.Context()
        socket = context.socket(zmq.ROUTER)
        socket.bind('ipc://./tmp/server' + str(self.sid))
        self.socket = socket
        self._addr = {}
        _addr, content = self.socket.recv_multipart()
        self._addr[msgpack.loads(content)] = _addr
        _addr, content = self.socket.recv_multipart()
        self._addr[msgpack.loads(content)] = _addr

    def _send(self, end=None):
        if not end:
            self.socket.send_multipart([
                self._addr[self.players_color[self.turn]],
                msgpack.dumps((self.turn, str(self.g.black),
                               str(self.g.white)))
            ])
        else:
            self.socket.send_multipart([
                self._addr[self.players_color['b']],
                msgpack.dumps((end, str(self.g.black), str(self.g.white)))
            ])
            self.socket.send_multipart([
                self._addr[self.players_color['w']],
                msgpack.dumps((end, str(self.g.black), str(self.g.white)))
            ])

    def _recv(self):
        _addr, content = self.socket.recv_multipart()
        return msgpack.loads(content)

    def _new_game(self):
        self.g.newround()
        self.turn = 'b'

    def _run_a_round(self):
        self._new_game()
        self.players_color = {'b': 0, 'w': 1}
        while True:
            self._send()
            who, x, y = self._recv()
            result = self.g.add(who, x, y)
            if result in 'BW':
                self._send(result)
                return
            elif result == 'F':
                print('##########')
            self.turn = 'w' if self.turn == 'b' else 'b'

    def run(self):
        self._buildsocket()
        for _ in range(100):
            self._run_a_round()
            print('Finish a round')
            self.g.show()


if __name__ == "__main__":
    server = Server(0)
    server.start()
