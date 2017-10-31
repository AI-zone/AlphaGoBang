# @Author: chenyu
# @Date:   20_Oct_2017
# @Email:  yu.chen@pku.edu.cn
# @Filename: __play__.py
# @Last modified by:   chenyu
# @Last modified time: 21_Oct_2017

import multiprocessing
import os
import time
import math
import zmq
import msgpack
import msgpack_numpy
import numpy as np
import math
import config

from ai.mcts_policy import Tree
from env.gobang import axis, legal, show_pi, toind, posswap
msgpack_numpy.patch()

selfplayfiles = os.listdir('/data/gobang/selfplay/')
selfplayfiles.sort()
selfplaylog = open('/data/gobang/selfplay/' + selfplayfiles[-1], 'a')


class Player(multiprocessing.Process):
    """
    一个Player同时玩K局，公用1个Tree，Tree的节点访问次数到1600就直接输出pi，
    否则继续扩展。这样不同对局累积下来的经验可以共享，效率高一些.
    """

    def __init__(self, sid, player_id):
        super().__init__()
        self.sid = sid
        self.player_id = player_id
        self.tree = Tree(self.sid, b'%d-%d' % (self.sid, self.player_id))
        self.memory = {}  # self.memory[t] = [(mine, yours), action, z]
        self.round_counter = 0

    def _buildsockets(self):
        sockets = {}
        context = zmq.Context()
        self.server_socket = context.socket(zmq.DEALER)
        self.server_socket.setsockopt_string(zmq.IDENTITY, str(self.player_id))
        self.server_socket.connect('ipc://./tmp/server' + str(self.sid))
        self.server_socket.send(msgpack.dumps(self.player_id))

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
            print(self.round_counter, len(self.tree.nodes))
            show_pi(board[1], board[2], pi)
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
        if end[0] == 'B':
            for t in self.memory:
                if t % 2 == 0:
                    self.memory[t][4] = 1
                else:
                    self.memory[t][4] = -1
        elif end[0] == 'W':
            for t in self.memory:
                if t % 2 == 0:
                    self.memory[t][4] = -1
                else:
                    self.memory[t][4] = 1
        elif end[0] == 'J':
            self.memory = {}
            return
            # for t in self.memory:
            #     if t % 2 == 0:
            #         self.memory[t][4] = -1
            #     else:
            #         self.memory[t][4] = 1
        elif end[0] == 'E':
            self.memory = {}
            return
        game_len = len(self.memory)
        for t in self.memory:
            if t % 2 == 0:
                serielized = [
                    str(self.memory[t][0]),
                    str(self.memory[t][1]),
                    str(self.memory[t][2]),
                    str(self.memory[t][3]),
                    str(self.memory[t][4] * math.pow(config.VALUE_DECAY,
                                                     game_len - t)),
                ]
            else:
                serielized = [
                    str(self.memory[t][1]),
                    str(self.memory[t][0]),
                    str(self.memory[t][2]),
                    str(self.memory[t][3]),
                    str(self.memory[t][4] * math.pow(config.VALUE_DECAY,
                                                     game_len - t)),
                ]
            print(','.join(serielized), file=selfplaylog)
        self.memory = {}
        self.round_counter += 1
        if self.round_counter % 100 == 0:
            self.tree = Tree(self.sid, b'%d-%d' % (self.sid, self.player_id))

    def _run_a_round(self):
        while True:
            board = self._recv_server()
            if isinstance(board[0], str):
                self._end_round(board)
                return
            pi = self._get_pi(board)
            action = self._get_action(board, pi)
            color = board[0] % 2
            self.memory[board[0]] = [
                board[1], board[2], color,
                toind(*action), 0
            ]
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
