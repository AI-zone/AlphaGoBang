"""MCTS"""
# pylint: disable-msg=C0103
# pylint: disable-msg=E1101
# pylint: disable-msg=E0632
import math
import queue
import time
import numpy as np
import config
from env.gobang import check, axis, gobit, legal

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


def _make_mask(action):
    if config.DISTANCE == 0:
        return 2**225 - 1
    x, y = axis(action)
    mask = 0
    for i in range(-config.DISTANCE, (config.DISTANCE + 1)):
        for j in range(-config.DISTANCE, (config.DISTANCE + 1)):
            mask += gobit[(x + i, y + j)]
    return mask


class Node():  # pylint: disable-msg=R0903
    """state node."""
    __slots__ = ['t', 'N', 'W', 'p', 'v', 'mask', 'updated']

    def __init__(self, t, mask):
        self.t = t
        self.N = 0
        self.W = 0
        self.mask = mask
        self.p = np.random.random(225).astype(np.float16)
        self.v = 0
        self.updated = False


class Tree():
    """MCTS."""
    __slots__ = [
        'nodes', 'mask', 'player_id', 'model_name', 'lock', 'to_evaluate'
    ]

    def __init__(self, player_id, lock):
        self.nodes = {}
        self.player_id = player_id
        self.model_name = player_id.split('_')[1]
        self.lock = lock
        self.to_evaluate = queue.Queue(maxsize=100000)

    def QnU(self, t, s_t, a, begin):
        """s_t: (black, white), a: action in [0, 224]. begin: global_step"""
        if t % 2 == 0:
            swap = 1
        else:
            swap = -1
        next_s, _ = move_state(t, *s_t, a, False)
        if t == begin:
            prior = config.ROOT_EXPLORE * np.random.random() + (
                1 - config.ROOT_EXPLORE) * self.nodes[s_t].p[a]
        else:
            prior = self.nodes[s_t].p[a]
        if next_s in self.nodes:
            if abs(self.nodes[next_s].W) > 0.05:
                Q = self.nodes[next_s].W / (self.nodes[next_s].N + 1)
            else:
                Q = self.nodes[next_s].v
            U = prior * math.sqrt(self.nodes[s_t].N) / (
                1 + self.nodes[next_s].N)
        else:
            Q = 0
            U = prior * math.sqrt(self.nodes[s_t].N)
        return swap * Q + U * config.VISIT_WEIGHT

    def _simulate(self, begin, simu_step, s_t, isleaf=0):
        """
        Args:
            begin:  global_step
            simu_step:  # moves from empty board
            s_t:    state at simu_step
            isleaf: when game is terminal, reward. 1 for win, -1 for ban
        """
        cur = self.nodes[s_t]
        while (cur.N > config.UPDATE_DELAY * config.NUM_SIMULATIONS) and (
                not cur.updated):
            time.sleep(0.01)
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
            return cur.v
        # 往下走
        empty = legal(s_t[0], s_t[1], simu_step)
        empty = [a for a in empty if gobit[axis(a)] & cur.mask]
        action = empty[np.argmax(
            [self.QnU(simu_step, s_t, a, begin) for a in empty])]
        s_tplus1, isleaf = move_state(simu_step, *s_t, action)
        if s_tplus1 not in self.nodes:
            #  create Node
            with self.lock:
                self.nodes[s_tplus1] = Node(simu_step + 1,
                                            cur.mask | _make_mask(action))
                self.to_evaluate.put((simu_step + 1, *s_tplus1))
        v = self._simulate(begin, simu_step + 1, s_tplus1, isleaf)
        with self.lock:
            cur.W += v
        return v

    def get_pi(self, t, black, white):
        """返回s_t状态开始的pi值， 注意：node永远是需要下棋的一方在第0张矩阵."""
        # if opponent move at ind and win,
        # I must move at ind.

        s_t = (black, white)
        if s_t not in self.nodes:
            #  create Node
            with self.lock:
                new_mask = gobit[(7, 7)]
                for ind in range(225):
                    if gobit[axis(ind)] & ((s_t[0] | s_t[1])):
                        new_mask = new_mask | _make_mask(ind)

                self.nodes[s_t] = Node(t, new_mask)
                self.to_evaluate.put((t, black, white))
        for ind in range(225):
            if not gobit[axis(ind)] & ((black | white)):
                if t % 2 == 0:
                    add = (black, white + gobit[axis(ind)])
                else:
                    add = (black + gobit[axis(ind)], white)
                if check(*add, *axis(ind), t + 1) == 1:
                    pi = np.zeros(225)
                    pi[ind] = config.NUM_SIMULATIONS * 0.99
                    return pi
        while self.nodes[s_t].N < config.NUM_SIMULATIONS:
            self._simulate(t, t, s_t)
            if s_t not in self.nodes:
                break
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
