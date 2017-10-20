# @Author: chenyu
# @Date:   20_Oct_2017
# @Email:  yu.chen@pku.edu.cn
# @Filename: __play__.py
# @Last modified by:   chenyu
# @Last modified time: 20_Oct_2017

import multiprocessing
import zmq
import msgpack
import msgpack_numpy
import numpy as np
import config

from ai.mcts_policy import Tree, Node

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
            self.tree.nodes[position] = Node(position)

    def _get_pi(self, board):
        """MCTS模拟config.NUM_SIMULATIONS，输出温度加权的次数分布"""
        for _ in range(config.NUM_SIMULATIONS):
            self._simulate(board)
        return np.random.random([225])

    def _send_decision(self, board, pi):
        """选择位置，并发送给server, 以及memory"""
        sum_pi = sum(pi)
        probs = [x / sum_pi for x in pi]
        ind = np.random.choice(list(range(225)), p=probs)
        self._send_server((board[0], ind // 15, ind % 15))

    def _end_round(self, board):
        pass

    def _run_a_round(self):
        while True:
            board = self._recv_server()
            if board[0] in "BW":
                self._end_round(board)
                return
            else:
                self.side = board[0]
            pi = self._get_pi(board)
            self._send_decision(board, pi)

    def run(self):
        np.random.seed()
        self._buildsockets()
        self._run_a_round()


if __name__ == "__main__":
    players = [Player(0, 0), Player(0, 1)]
    for p in players:
        p.start()
