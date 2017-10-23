# @Author: chenyu
# @Date:   20_Oct_2017
# @Email:  yu.chen@pku.edu.cn
# @Filename: __play__.py
# @Last modified by:   chenyu
# @Last modified time: 21_Oct_2017

import multiprocessing
import time
import zmq
import msgpack
import msgpack_numpy
import numpy as np
import math
import config

from ai.mcts_policy import Tree
from env.gobang import axis, legal, show, toind
msgpack_numpy.patch()

warmup_file = open('/data/gobang/warmup', 'a')


class Player(multiprocessing.Process):
    """
    一个Player同时玩K局，公用1个Tree，Tree的节点访问次数到1600就直接输出pi，
    否则继续扩展。这样不同对局累积下来的经验可以共享，效率高一些.
    """

    def __init__(self, sid, player_id):
        super().__init__()
        self.sid = sid
        self.tree = Tree()
        self.side = None  # black or white, depends on server
        self.player_id = player_id
        self.memory = {}  # self.memory[t] = [(mine, yours), action, z]
        self.round_counter = 0

    def _buildsockets(self):
        sockets = {}
        context = zmq.Context()
        self.server_socket = context.socket(zmq.DEALER)
        self.server_socket.setsockopt_string(zmq.IDENTITY, str(self.player_id))
        self.server_socket.connect('ipc://./tmp/server' + str(self.sid))
        self.server_socket.send(msgpack.dumps(self.player_id))
        # self.net_socket = context.socket(zmq.DEALER)
        # self.net_socket.connect('ipc://./tmp/net' + str(self.sid))
        print("FINISH build socket")

    def _recv_server(self):
        """从server接收board局势."""
        content = self.server_socket.recv()
        content = msgpack.loads(content)
        content[1] = int(content[1])
        content[2] = int(content[2])
        return content

    def _send_server(self, content):
        self.server_socket.send(msgpack.dumps(content))

    def _get_inference(self, content):
        """通过zmq向inference询问pv"""
        return np.random.random([226])

    def _get_pi(self, board):
        """board=t,black,white"""
        return self.tree.get_pi(*board)

    def _get_action(self, board, pi):
        """按pi 温度加权抽样"""
        if self.sid == 0:
            # only print server 0
            print(self.round_counter)
            show(board[1], board[2])
        if config.TEMPERATURE == 0:
            ind = np.argmax(pi)
            return axis(ind)
        empty = legal(board[1], board[2], board[0])
        temperature_pi = [
            math.pow(pi[i], 1 / config.TEMPERATURE) for i in empty
        ]
        sum_pi = sum(temperature_pi)
        probs = [
            math.pow(pi[i], 1 / config.TEMPERATURE) / sum_pi for i in empty
        ]
        ind = np.random.choice(empty, p=probs)
        return axis(ind)

    def _end_round(self, end):
        if end == 'B':
            for t in self.memory:
                if t % 2 == 0:
                    self.memory[t][3] = 1
                else:
                    self.memory[t][3] = -1
        elif end == 'W':
            for t in self.memory:
                if t % 2 == 0:
                    self.memory[t][3] = -1
                else:
                    self.memory[t][3] = 1
        for t in self.memory:
            serielized = [str(i) for i in self.memory[t]]
            print(','.join(serielized), file=warmup_file)
        self.memory = {}
        self.round_counter += 1
        if self.round_counter % 100 == 0:
            self.tree = Tree()

    def _run_a_round(self):
        while True:
            board = self._recv_server()
            if isinstance(board[0], str):
                self._end_round(board)
                return
            pi = self._get_pi(board)
            action = self._get_action(board, pi)
            if board[0] % 2 == 0:
                mine, yours = board[1], board[2]
            else:
                mine, yours = board[2], board[1]

            self.memory[board[0]] = [mine, yours, toind(*action), 0]
            self._send_server(action)

    def run(self):
        np.random.seed()
        self._buildsockets()
        while True:
            self._run_a_round()


if __name__ == "__main__":
    players = [
        Player(sid, i)
        for i in range(config.MODE) for sid in range(config.NUMPARALELL)
    ]
    for p in players:
        p.start()
