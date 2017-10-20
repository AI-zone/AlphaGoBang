# @Author: chenyu
# @Date:   20_Oct_2017
# @Email:  yu.chen@pku.edu.cn
# @Filename: inference.py
# @Last modified by:   chenyu
# @Last modified time: 20_Oct_2017

import numpy as np
from env.gobang import valid, check, axis, Game


class Node():
    def __init__(self, t, mine, yours):
        """"建一个搜索树的节点
        t: 棋盘中的总棋子ge个数，可以用来判断value的正负以及谁赢了.
        s_t: t为偶数，该黑子下棋了
        mine, yours 是相对于t的，player总假设现在该自己下.
        """
        self.t = t
        self.N = 0
        self.W = 0
        self.v, self.p = self._get_p_v(mine, yours)

    def _get_p_v(self, mine, yours):
        return np.random.random(225), np.random.random()


class Edge():
    pass


class Tree():
    """MCTS."""

    def __init__(self):
        self.nodes = {}

    def _get_pi(self, s_t):
        return np.random.random(225)
