"""MCTD"""
# pylint: disable-msg=C0103
# pylint: disable-msg=E1101
# pylint: disable-msg=E0632
import sys
import numpy as np
import math
import random
import config
import zmq
import msgpack
import msgpack_numpy
from env.gobang import valid, check, axis, gobit, legal, show, posswap
import numpy as np
msgpack_numpy.patch()

import threading

lock = threading.Lock()

# pylint: disable-msg=C0103


def move_state(t, black, white, a, check_win=True):
    """
    Return:
        state: (black, white)
        point:  1 if the player move at time t win
               -1 if the black move at time t is banned.
    """
    if t % 2 == 0:
        black += gobit[axis(a)]
    else:
        white += gobit[axis(a)]
    if check_win:
        point = check(black, white, *axis(a), t)
    else:
        point = 0
    return (black, white), point


def make_mask(action):
    if config.DISTANCE == 0:
        return 2**225 - 1
    x, y = axis(action)
    mask = 0
    for i in range(-config.DISTANCE, (config.DISTANCE + 1)):
        for j in range(-config.DISTANCE, (config.DISTANCE + 1)):
            mask += gobit[(x + i, y + j)]
    return mask


class Node():
    """state node."""
    __slots__ = ['t', 'N', 'W', 'mine', 'yours', 'p', 'v', 'mask']

    def __init__(self, t, black, white, mask):
        """
        """
        self.t = t
        self.N = 0
        self.W = 0
        self._get_p_v(t, *posswap(t, black, white))
        self.mask = mask

    def _get_p_v(self, t, mine, yours):
        p, v = np.random.random(225).astype(np.float16), np.random.random()
        self.p = p
        if t % 2 == 0:
            self.v = v
        else:
            self.v = -v


class Tree():
    """MCTS."""
    __slots__ = ['nodes', 'mask', 'socket', 'player_id', 'model_name', 'lock']

    def __init__(self, player_id, lock):
        self.nodes = {}
        self.socket = None
        self.player_id = player_id
        self.model_name = player_id.split('_')[1]
        self._buildsockets()
        self.lock = lock

    def _buildsockets(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.DEALER)
        self.socket.setsockopt_string(zmq.IDENTITY, self.player_id)
        self.socket.connect('ipc://./tmp/oracle_%s' % self.model_name)

    def QnU(self, t, s_t, a, begin):
        """s_t: (black, white), a: action in [0, 224]. begin: global_step"""
        if begin % 2 == 0:
            swap = 1
        else:
            swap = -1
        next_s, _ = move_state(t, *s_t, a, False)
        if next_s in self.nodes:
            Q = self.nodes[next_s].W / (self.nodes[next_s].N + 1)
            U = self.nodes[s_t].p[a] * math.sqrt(self.nodes[s_t].N) / (
                1 + self.nodes[next_s].N)
        else:
            Q = 0
            U = self.nodes[s_t].p[a] * math.sqrt(self.nodes[s_t].N)
        return swap * Q + U * config.EXPLORATION

    def _simulate(self, begin, simu_step, s_t, isleaf=0):
        """
        Args:
            begin:  global_step
            simu_step:  # moves from empty board
            s_t:    state at simu_step
            isleaf: when game is terminal, reward. 1 for win, -1 for ban
        """
        cur = self.nodes[s_t]
        with self.lock:
            cur.N += 1
            if isleaf == 1:
                if simu_step % 2 == 1:  # black win
                    cur.W += 1
                    return 1
                # white win
                cur.W += -1
                return -1
            elif isleaf == -1:
                if simu_step % 2 == 1:  # black ban
                    cur.W += -1
                    return -1

        if simu_step >= begin + config.L:
            # return self.nodes[s_t].v
            return 0
        # 往下走
        empty = legal(s_t[0], s_t[1], simu_step)
        empty = [a for a in empty if gobit[axis(a)] & cur.mask]
        action = empty[np.argmax(
            [self.QnU(simu_step, s_t, a, begin) for a in empty])]
        s_tplus1, isleaf = move_state(simu_step, *s_t, action)
        if s_tplus1 not in self.nodes:
            #  create Node
            with self.lock:
                self.nodes[s_tplus1] = Node(simu_step + 1, *s_tplus1,
                                            cur.mask | make_mask(action))
        v = self._simulate(begin, simu_step + 1, s_tplus1, isleaf)
        with self.lock:
            cur.W += v
        return v

    def get_pi(self, t, black, white):
        """返回s_t状态开始的pi值， 注意：node永远是需要下棋的一方在第0张矩阵."""
        s_t = (black, white)
        if s_t not in self.nodes:
            #  create Node
            with self.lock:
                new_mask = gobit[(7, 7)]
                for ind in range(225):
                    if gobit[axis(ind)] & ((s_t[0] | s_t[1])):
                        new_mask = new_mask | make_mask(ind)

                self.nodes[s_t] = Node(t, *s_t, new_mask)

        while self.nodes[s_t].N < config.NUM_SIMULATIONS:
            self._simulate(t, t, s_t)
        empty = legal(s_t[0], s_t[1], t)
        pi = np.zeros(225)
        for a in empty:
            next_s = move_state(t, *s_t, a)[0]
            if next_s not in self.nodes:
                continue
            pi[a] = self.nodes[next_s].N
        return pi


if __name__ == "__main__":
    pass
