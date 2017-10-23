import sys
sys.path.append("/Users/chenyu/dllab/AlphaGoBang/")
import numpy as np
import math
import random
import config
from env.gobang import valid, check, axis, gobit, legal, show


def plot_pi(mine, yours, pi):
    pi = pi / sum(pi) * 100
    pi = pi.reshape((15, 15)).T
    for x in range(15):
        for y in range(15):
            if (mine & gobit[(x, y)]):
                print("\033[%d;%d;%dm  \033[0m" % (0, 31, 41), end='')
            elif (yours & gobit[(x, y)]):
                print("\033[%d;%d;%dm  \033[0m" % (0, 32, 42), end='')
            elif int(pi[x, y]) >= 1:
                print("%2d" % int(pi[x, y]), end='')
            else:
                print("  ", end='')
        print("")


# @profile
def move_state(mine, yours, a, check_win=True):
    mine += gobit[axis(a)]
    if check_win:
        point = check(mine, yours, *axis(a))
    else:
        point = 0
    return (yours, mine), point


def make_mask(action):
    x, y = axis(action)
    mask = 0
    for i in range(-config.DISTANCE, (config.DISTANCE + 1)):
        for j in range(-config.DISTANCE, (config.DISTANCE + 1)):
            mask += gobit[(x + i, y + j)]
    return mask


class Node():
    __slots__ = ['t', 'N', 'W', 'mine', 'yours', 'p', 'v', 'mask']

    def __init__(self, t, mine, yours, mask):
        """"建一个搜索树的节点. 注意：node永远是需要下棋的一方在第0张矩阵
        t: 棋盘中的总棋子ge个数，可以用来判断value的正负以及谁赢了.
        s_t: t为偶数，该黑子下棋了
        mine, yours 是相对于t的，player总假设现在该自己下.
        """
        self.t = t
        self.N = 0
        self.W = 0
        self.get_p_v(mine, yours)
        self.mine = mine
        self.yours = yours
        self.mask = mask

    # @profile
    def get_p_v(self, mine, yours):
        """首次访问时候调用, 建立时不用调用
        例如父节点选边，子节点的v暂时当0，叶子节点（simulate结束时需要调用v）"""
        self.p, self.v = np.random.random(225), np.random.random()


class Tree():
    """MCTS."""
    __slots__ = ['nodes', 'mask']

    def __init__(self):
        self.nodes = {}

    # @profile
    def QnU(self, s_t, a):
        """返回行动a的Q, a:0-224."""
        next_s, isleaf = move_state(*s_t, a, False)
        if next_s in self.nodes:
            Q = self.nodes[next_s].W / self.nodes[next_s].N
            U = self.nodes[s_t].p[a] * math.sqrt(self.nodes[s_t].N) / (
                1 + self.nodes[next_s].N)
        else:
            Q = 0
            U = self.nodes[s_t].p[a] * math.sqrt(self.nodes[s_t].N)
        return Q + U

    # @profile
    def _simulate(self, begin, simu_step, s_t, isleaf=0):
        """从s_t开始往下走, 已经走了simu_step步."""
        cur = self.nodes[s_t]
        cur.N += 1
        if isleaf == 1:
            # 因为走了下一步，所以begin与simu_step 奇偶不同则赢
            if (simu_step - begin) % 2 == 1:
                cur.W += 1
                return 1
            cur.W += -1
            return -1
        elif isleaf == -1:
            # 奇数时间，表示上一步黑子，禁手
            if simu_step % 2 == 1:
                if begin % 2 == 0:
                    cur.W += -1
                    return -1
                cur.W += 1
                return 1
        if simu_step >= begin + config.L:
            # return self.nodes[s_t].v
            return 0
        # 往下走
        empty = legal(s_t[0], s_t[1], simu_step)
        empty = [a for a in empty if gobit[axis(a)] & cur.mask]
        action = empty[np.argmax([self.QnU(s_t, a) for a in empty])]
        s_tplus1, isleaf = move_state(*s_t, action)
        if s_tplus1 not in self.nodes:
            #  见过就复用，否则创建新节点
            self.nodes[s_tplus1] = Node(simu_step + 1, *s_tplus1,
                                        cur.mask | make_mask(action))
        v = self._simulate(begin, simu_step + 1, s_tplus1, isleaf)
        if v == 0:
            #  乱下没结果
            cur.W += config.PUNISH * (simu_step - begin) / simu_step
        else:
            cur.W += v
        return v

    # @profile
    def get_pi(self, t, black, white):
        """返回s_t状态开始的pi值， 注意：node永远是需要下棋的一方在第0张矩阵."""
        s_t = (black, white) if t % 2 == 0 else (white, black)
        if s_t not in self.nodes:
            #  见过就复用，否则创建新节点
            new_mask = gobit[(7, 7)]
            for ind in range(255):
                if gobit[axis(ind)] & (s_t[0] | s_t[1]):
                    new_mask = new_mask | make_mask(ind)
            self.nodes[s_t] = Node(t, *s_t, new_mask)
        while self.nodes[s_t].N < config.NUM_SIMULATIONS:
            self._simulate(t, t, s_t)
        empty = legal(s_t[0], s_t[1], t)
        pi = np.zeros(225)
        for a in empty:
            next_s = move_state(*s_t, a)[0]
            if next_s not in self.nodes:
                continue
            pi[a] = self.nodes[next_s].N
        return pi


if __name__ == "__main__":
    tree = Tree()
    tree.get_pi(0, 0, 0)
