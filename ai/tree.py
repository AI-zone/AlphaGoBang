# @Author: chenyu
# @Date:   19_Oct_2017
# @Email:  yu.chen@pku.edu.cn
# @Filename: tree.py
# @Last modified by:   chenyu
# @Last modified time: 20_Oct_2017


class TreeNode():
    def __init__(self, s):
        self.s = s
        self.v = 0  # visits


class TreeEdge():
    def __init__(self, s, a):
        self.s = s
        self.a = a
        self.n = 0
        self.w = 0  # total action value
        self.p = 0  # action select probability
