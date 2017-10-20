# @Author: chenyu
# @Date:   20_Oct_2017
# @Email:  yu.chen@pku.edu.cn
# @Filename: __play__.py
# @Last modified by:   chenyu
# @Last modified time: 21_Oct_2017

import multiprocessing
import zmq
import msgpack
import msgpack_numpy
import numpy as np
import config

from ai.mcts_policy import Tree, Node
from env.gobang import axis, valid
msgpack_numpy.patch()


class Player(multiprocessing.Process):
    """你来写"""

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

    def _simulate(self, board):
        """迭代着_get_inference, select, expand, backup. 没有return"""
        position = (board[2], board[2])
        if position in self.tree.nodes:
            # 复用
            node = self.tree.nodes[position]
        else:
            self.tree.nodes[position] = Node(*board)

    def _get_pi(self, board):
        """MCTS模拟config.NUM_SIMULATIONS，输出温度加权的次数分布"""
        for _ in range(config.NUM_SIMULATIONS):
            self._simulate(board)
        return np.random.random([225])

    def _get_action(self, board, pi):
        """按pi 温度加权抽样"""
        temperature_pi = [np.power(x, config.TEMPERATURE) for x in pi]
        sum_pi = sum(temperature_pi)
        probs = [np.power(x, config.TEMPERATURE) / sum_pi for x in pi]
        ind = np.random.choice(list(range(225)), p=probs)
        while not valid(board[1], board[2], *axis(ind)):
            ind = np.random.choice(list(range(225)), p=probs)
        return axis(ind)

    def _end_round(self, board):
        pass

    def _run_a_round(self):
        while True:
            board = self._recv_server()
            if board[0] < 0:
                self._end_round(board)
                return

            pi = self._get_pi(board)
            action = self._get_action(board, pi)
            self._send_server(action)

    def run(self):
        np.random.seed()
        self._buildsockets()
        self._run_a_round()


if __name__ == "__main__":
    players = [Player(0, 0), Player(0, 1)]
    for p in players:
        p.start()
