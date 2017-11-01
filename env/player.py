"""Player"""
# pylint: disable-msg=C0103
# pylint: disable-msg=E1101
# pylint: disable-msg=E0632

import multiprocessing
import threading
import os
import math
import zmq
import msgpack
import msgpack_numpy
import numpy as np
import config

from ai.mcts_policy import Tree
from env.gobang import axis, legal, show_pi, toind, posswap
msgpack_numpy.patch()


def _recv_server(socket):
    """Return state:  t(or BWJE), black, white.
    """
    content = socket.recv()
    content = msgpack.loads(content)
    content[1] = int(content[1])
    content[2] = int(content[2])
    return content


def _send_server(socket, content):
    socket.send(msgpack.dumps(content))


class Player(multiprocessing.Process):
    """Player.
    Properties:
        tree:   shared MCTS
        memory: dictionary with key time and
                value [mine, yours, color, action, value]
    """

    def __init__(self, server_id, player_id):
        super().__init__()
        self.server_id = server_id
        self.player_id = player_id
        self.memory = {}
        self.log_writter = open('/data/gobang/selfplay/%s--%s' %
                                (server_id, player_id), 'a')
        self.lock = threading.Lock()
        self.tree = Tree(self.player_id, self.lock)

    def _get_pi(self, board):
        """board=t,black,white"""
        return self.tree.get_pi(*board)

    def _get_action(self, board, pi, gid):
        """sample according to pi(with config.TENPERATURE)"""
        if gid == 0:
            print(len(self.tree.nodes), self.tree.to_evaluate.qsize())
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

    def _end_round(self, end):  # pylint: disable-msg=R0912
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
            print(','.join(serielized), file=self.log_writter)
        self.memory = {}

    def _run_infinite_round(self, gid):
        np.random.seed()
        context = zmq.Context()
        socket = context.socket(zmq.DEALER)
        socket.setsockopt(zmq.IDENTITY,
                          bytes('%s-%d' % (self.player_id, gid), 'utf8'))
        socket.connect('ipc://./tmp/server_' + str(self.server_id))
        socket.send(msgpack.dumps(self.player_id))
        while True:
            board = _recv_server(socket)
            if isinstance(board[0], str):
                self._end_round(board)
                continue
            pi = self._get_pi(board)
            action = self._get_action(board, pi, gid)
            color = board[0] % 2
            self.memory[board[0]] = [
                board[1], board[2], color,
                toind(*action), 0
            ]
            _send_server(socket, (*action, gid))

    def evaluate_node(self):
        """update node p, v in tree"""
        # p, v = np.random.random(225).astype(np.float16), np.random.random()
        context = zmq.Context()
        socket = context.socket(zmq.DEALER)
        socket.setsockopt_string(zmq.IDENTITY, self.player_id)
        socket.connect('ipc://./tmp/oracle_%s' % self.tree.model_name)
        print('start to evaluate', self.tree.model_name)
        while True:
            # print(self.tree.to_evaluate.qsize())
            batch = []
            for _ in range(config.INFERENCE_BATCHSIZE):
                t, black, white = self.tree.to_evaluate.get()
                mine, yours = posswap(t, black, white)
                color = t % 2
                batch.append((str(mine), str(yours), color))

            socket.send(msgpack.dumps((batch, self.player_id)))
            result = socket.recv()

    def run(self):
        threads = []
        for i in range(config.GAMEPARALELL):
            t = threading.Thread(target=self._run_infinite_round, args=(i, ))
            t.daemon = True
            threads.append(t)
            t.start()
        evaluate_thread = threading.Thread(target=self.evaluate_node)
        threads.append(evaluate_thread)
        evaluate_thread.start()
        for t in threads:
            t.join()


if __name__ == "__main__":
    pass
