# @Author: chenyu
# @Date:   20_Oct_2017
# @Email:  yu.chen@pku.edu.cn
# @Filename: inference.py
# @Last modified by:   chenyu
# @Last modified time: 21_Oct_2017

import numpy as np
import math
import config
from env.gobang import valid, check, axis, gobit, Game


class Node():
    def __init__(self, t, mine, yours):
        """"建一个搜索树的节点. 注意：node永远是需要下棋的一方在第0张矩阵
        t: 棋盘中的总棋子ge个数，可以用来判断value的正负以及谁赢了.
        s_t: t为偶数，该黑子下棋了
        mine, yours 是相对于t的，player总假设现在该自己下.
        """
        self.t = t
        self.N = 0
        self.W = 0

        self.children = {}  # key of children is 0-224

    @property
    def Q(self, a):
        """返回行动a的Q, a:0-224."""
        return self.children[a].W / self.children[a].N

    @property
    def U(self, a):
        """s状态对应的节点, 返回行动a的U(s,a) a:0-224."""
        return config.EXPLORATION * self.p[a] * math.sqrt(self.N) / (
            1 + self.children[a].N)

    def get_p_v(self, mine, yours):
        """首次访问时候调用, 建立时不用调用
        例如父节点选边，子节点的v暂时当0，叶子节点（simulate结束时需要调用v）"""
        self.v, self.p = np.random.random(225), np.random.random()


class Tree():
    """MCTS."""

    def __init__(self):
        self.nodes = {}

    def _move_state(self, s_t, a):
        if valid(*s_t, *axis(a)):
            s_t[0] += gobit[axis(a)]
        else:
            raise RuntimeError("duplicated move in simulation.")
        if check(s_t[0], *axis(a)) == "P":
            return (s_t[1], s_t[0])
        return -1, -1

    def _simulate(self, s_t):
        """迭代着_get_inference, select, expand, backup. 没有return"""
        self.nodes[s_t].N += 1

    def get_pi(self, t, black, white):
        """返回s_t状态开始的pi值， 注意：node永远是需要下棋的一方在第0张矩阵"""
        s_t = (black, white) if t % 2 == 0 else (white, black)
        if s_t not in self.nodes:
            #  见过就复用，否则创建新节点
            self.nodes[s_t] = Node(t, *s_t)
        root = self.nodes[s_t]
        while root.N < config.NUM_SIMULATIONS:
            self._simulate(s_t)
        return np.random.random(225)
