import sys
sys.path.append("/Users/chenyu/dllab/AlphaGoBang/")
import numpy as np
import math
import random
import config
from env.gobang import valid, check, axis, gobit, legal, show


# @profile
def move_state(mine, yours, a, check_win=True):
    mine += gobit[axis(a)]
    if check_win:
        if not check(mine, *axis(a)):
            return (yours, mine), False
    return (yours, mine), True


class Node():
    __slots__ = ['t', 'N', 'W', 'mine', 'yours', 'p', 'v']

    def __init__(self, t, mine, yours):
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

    # @profile
    def get_p_v(self, mine, yours):
        """首次访问时候调用, 建立时不用调用
        例如父节点选边，子节点的v暂时当0，叶子节点（simulate结束时需要调用v）"""
        self.p, self.v = np.random.random(225), np.random.random()


class Tree():
    """MCTS."""
    __slots__ = ['nodes']

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
    def _simulate(self, simu_step, s_t, isleaf=False):
        """从s_t开始往下走, 已经走了simu_step步."""
        cur = self.nodes[s_t]
        cur.N += 1
        if isleaf:
            print('############')
            if simu_step % 2 == 1:
                return 1
            return 0

        if simu_step >= config.L:
            # return self.nodes[s_t].v
            return 0
        # 往下走
        empty = legal(s_t[0], s_t[1])
        empty = random.sample(empty, (1 + int(0.1 * len(empty))))
        action = empty[np.argmax([self.QnU(s_t, a) for a in empty])]
        s_tplus1, isleaf = move_state(*s_t, action)
        if s_tplus1 not in self.nodes:
            #  见过就复用，否则创建新节点
            self.nodes[s_tplus1] = Node(simu_step + 1, *s_tplus1)
        v = self._simulate(simu_step + 1, s_tplus1, isleaf)
        cur.W += v
        return v

    # @profile
    def get_pi(self, t, black, white):
        """返回s_t状态开始的pi值， 注意：node永远是需要下棋的一方在第0张矩阵."""
        s_t = (black, white) if t % 2 == 0 else (white, black)
        if s_t not in self.nodes:
            #  见过就复用，否则创建新节点
            self.nodes[s_t] = Node(t, *s_t)
        while self.nodes[s_t].N < config.NUM_SIMULATIONS:
            self._simulate(t, s_t)
            print(self.nodes[s_t].N)
        empty = legal(s_t[0], s_t[1])
        pi = {}
        for a in empty:
            next_s = move_state(*s_t, a)[0]
            if next_s not in self.nodes:
                continue
            pi[axis(a)] = self.nodes[next_s].N
        print(sorted(pi.items(), key=lambda a: a[1], reverse=True))
        sys.exit(0)
        return np.random.random(225)


if __name__ == "__main__":
    tree = Tree()
    tree.get_pi(0, 0, 0)
