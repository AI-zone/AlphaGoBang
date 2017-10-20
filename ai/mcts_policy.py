# @Author: chenyu
# @Date:   20_Oct_2017
# @Email:  yu.chen@pku.edu.cn
# @Filename: inference.py
# @Last modified by:   chenyu
# @Last modified time: 20_Oct_2017

import numpy as np


class Node():
    def __init__(self, board):
        pass


class Edge():
    pass


class Tree():
    """MCTS."""

    def __init__(self):
        self.nodes = {}

    def _get_pi(self, s_t):
        return np.random.random(225)
