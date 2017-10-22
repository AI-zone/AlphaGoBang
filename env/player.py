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
import matplotlib.pyplot as plt
import config

from ai.mcts_policy import Tree, Node
from env.gobang import axis, valid, legal, gobit
msgpack_numpy.patch()


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
        empty = legal(board[1], board[2], board[0])
        temperature_pi = [math.pow(pi[i], config.TEMPERATURE) for i in empty]
        sum_pi = sum(temperature_pi)
        probs = [math.pow(pi[i], config.TEMPERATURE) / sum_pi for i in empty]
        ind = np.random.choice(empty, p=probs)
        return axis(ind)

    def _end_round(self, board):
        pass

    def _run_a_round(self):
        while True:
            board = self._recv_server()
            if board[0] < 0:
                self._end_round(board)
                return
            tstart = time.time()
            pi = self._get_pi(board)
            action = self._get_action(board, pi)
            print(board[0], time.time() - tstart)
            # # print in qtconsole
            # img_show_mat = np.reshape(pi, (15, 15)) / np.max(pi)
            # black = board[1]
            # white = board[2]
            # for ind in range(255):
            #     x, y = axis(ind)
            #     if gobit[(x, y)] & black:
            #         img_show_mat[x, y] = -1
            #     if gobit[(x, y)] & white:
            #         img_show_mat[x, y] = -2
            # plt.imshow(img_show_mat)
            # plt.show()
            self._send_server(action)

    def run(self):
        np.random.seed()
        self._buildsockets()
        while True:
            self._run_a_round()


if __name__ == "__main__":
    players = [Player(0, i) for i in range(config.MODE)]
    for p in players:
        p.start()
