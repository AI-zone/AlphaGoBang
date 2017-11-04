"""Player"""
# pylint: disable-msg=C0103
# pylint: disable-msg=E1101
# pylint: disable-msg=E0632

import multiprocessing
import threading
import time
import math
import zmq
import msgpack
import msgpack_numpy
import numpy as np
import config

from ai.mcts_policy import Tree, move_state
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


class Player(multiprocessing.Process):  # pylint: disable-msg=R0902
    """Player.
    Properties:
        tree:   shared MCTS
        memory: dictionary with key time and
                value [mine, yours, color, action, value]
    """

    def __init__(self, server_id, player_id, showlog):
        super().__init__()
        self.server_id = server_id
        self.player_id = player_id
        self.memory = {i: {} for i in range(config.GAMEPARALELL)}
        self.log_writter = open('/data/gobang/selfplay/%s' % server_id, 'a')
        self.lock = threading.Lock()
        self.tree = Tree(self.player_id, self.lock)
        self.showlog = showlog
        self.age = 0

    def _get_pi(self, board):
        """board=t,black,white"""
        return self.tree.get_pi(*board)

    def _get_action(self, board, pi, gid):
        """sample according to pi(with config.TENPERATURE)"""
        if (gid == 0) and self.showlog:
            print(
                'player:%s, age:%d, IQ:%d, learning:%d' %
                (self.player_id, self.age, len(self.tree.nodes),
                 self.tree.to_evaluate.qsize()),
                end='\t')
            if board[0] % 2 == 0:
                print("\033[%d;%d;%dm BLACK \033[0m" % (0, 37, 41))
            else:
                print("\033[%d;%d;%dm WHITE \033[0m" % (0, 37, 42))
            values = np.zeros(225)
            Q = np.zeros(225)
            for move in range(225):
                s_next, _ = move_state(*board, move, False)
                if s_next in self.tree.nodes:
                    values[move] = self.tree.nodes[s_next].v
                    Q[move] = self.tree.nodes[s_next].W / (
                        1 + self.tree.nodes[s_next].N)
            show_pi(board[1], board[2], pi,
                    self.tree.nodes[(board[1], board[2])].p, values, Q)
        if config.TEMPERATURE(board[0]) == 0:
            ind = np.argmax(pi)
            return axis(ind)
        empty = legal(board[1], board[2], board[0])
        temperature_pi = [
            math.pow(pi[i], 1 / config.TEMPERATURE(board[0])) for i in empty
        ]
        sum_pi = sum(temperature_pi)
        probs = [
            math.pow(pi[i], 1 / config.TEMPERATURE(board[0])) / sum_pi
            for i in empty
        ]
        ind = np.random.choice(empty, p=probs)
        return axis(ind)

    def _end_round(self, end, gid):  # pylint: disable-msg=R0912
        if end[0] == 'B':
            for t in self.memory[gid]:
                if t % 2 == 0:
                    self.memory[gid][t][4] = 1
                else:
                    self.memory[gid][t][4] = -1
        elif end[0] == 'W':
            for t in self.memory[gid]:
                if t % 2 == 0:
                    self.memory[gid][t][4] = -1
                else:
                    self.memory[gid][t][4] = 1
        elif end[0] == 'J':
            for t in self.memory[gid]:
                if t % 2 == 0:
                    self.memory[gid][t][4] = -1
                else:
                    self.memory[gid][t][4] = 1

        elif end[0] == 'E':
            for t in self.memory[gid]:
                if t % 2 == 0:
                    self.memory[gid][t][4] = -config.WHITE_ALLOWANCE
                else:
                    self.memory[gid][t][4] = config.WHITE_ALLOWANCE

        game_len = len(self.memory[gid])
        for t in self.memory[gid]:
            if t % 2 == 0:
                serielized = [
                    str(self.memory[gid][t][0]),
                    str(self.memory[gid][t][1]),
                    str(self.memory[gid][t][2]),
                    str(self.memory[gid][t][3]),
                    str(self.memory[gid][t][4] * math.pow(
                        config.VALUE_DECAY, game_len - t)),
                ]
            else:
                serielized = [
                    str(self.memory[gid][t][1]),
                    str(self.memory[gid][t][0]),
                    str(self.memory[gid][t][2]),
                    str(self.memory[gid][t][3]),
                    str(self.memory[gid][t][4] * math.pow(
                        config.VALUE_DECAY, game_len - t)),
                ]

            print(','.join(serielized), file=self.log_writter)
        self.memory[gid] = {}
        self.age += 1

    def _run_infinite_round(self, gid):
        np.random.seed()
        context = zmq.Context()
        socket = context.socket(zmq.DEALER)
        socket.setsockopt(zmq.IDENTITY,
                          bytes('%s-%d' % (self.player_id, gid), 'utf8'))
        socket.connect('ipc://./tmp/server_' + str(self.server_id))
        socket.send(msgpack.dumps(self.player_id))
        for _ in range(config.REBORN):
            board = _recv_server(socket)
            if str(board[0]) in 'BWJE':
                with self.lock:
                    self._end_round(board, gid)
                continue
            pi = self._get_pi(board)
            action = self._get_action(board, pi, gid)
            color = board[0] % 2
            self.memory[gid][board[0]] = [
                board[1], board[2], color,
                toind(*action), 0
            ]
            socket.send(msgpack.dumps((*action, gid)))

    def evaluate_node(self):
        """update node p, v in tree"""
        # p, v = np.random.random(225).astype(np.float16), np.random.random()
        socket = zmq.Context().socket(zmq.DEALER)
        socket.setsockopt_string(zmq.IDENTITY, self.player_id)
        socket.connect('ipc://./tmp/oracle_%s' % self.tree.model_name)
        print('start to evaluate', self.tree.model_name)
        while True:
            # print(self.tree.to_evaluate.qsize())
            batch = []
            states = []
            colors = []
            size = self.tree.to_evaluate.qsize()
            if size > config.INFERENCE_BATCHSIZE:
                size = config.INFERENCE_BATCHSIZE
            elif size == 0:
                time.sleep(0.001)
                continue
            for _ in range(size):
                t, black, white = self.tree.to_evaluate.get()
                mine, yours = posswap(t, black, white)
                batch.append((str(mine), str(yours), t % 2))
                states.append((black, white))
                colors.append(t % 2)
            socket.send(msgpack.dumps((batch, self.player_id)))
            result = msgpack.loads(socket.recv())
            assert len(states) == len(result[0])
            assert len(states) == len(result[1])
            for ind, state in enumerate(states):
                with self.lock:
                    self.tree.nodes[state].p = result[0][ind]
                    if colors[ind] == 0:
                        self.tree.nodes[state].v = result[1][ind]
                    else:
                        self.tree.nodes[state].v = -result[1][ind]
                    self.tree.nodes[state].updated = True

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
