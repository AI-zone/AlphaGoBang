#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug  5 22:04:19 2017

@author: chenyu
"""

import config
import pickle
import numpy as np

try:
    complete5, open4, open3 = pickle.load(open('./env/cached.pkl', 'rb'))
except:
    complete5, open4, open3 = 0, 0, 0
    print("run env/cache.py first")
X = [0x0, 0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8, 0x9, 0xa, 0xb, 0xc, 0xd, 0xe]
Y = [0x0, 0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8, 0x9, 0xa, 0xb, 0xc, 0xd, 0xe]

gobit = {}
for x in range(-10, 25):
    for y in range(-10, 25):
        gobit[(x, y)] = 0
for x in X:
    for y in Y:
        gobit[(x, y)] = 2**(x + 15 * y)

mask_col = [sum([gobit[(x, y)] for x in range(15)]) for y in range(15)]
mask_row = [sum([gobit[(x, y)] for y in range(15)]) for x in range(15)]
mask_zheng = [0] * 30
mask_fan = [0] * 30
for x in X:
    for y in Y:
        mask_zheng[x + y] += gobit[(x, y)]
        mask_fan[14 - x + y] += gobit[(x, y)]


# @profile
def axis(ind):
    return ind % 15, ind // 15


def toind(x, y):
    return x + 15 * y


def int2array(line, augment=True):
    """
    line: [mine, yours, color, action, value]
    return: example, policy, value lis

    """
    example = np.zeros((15, 15, 3), dtype=np.float32)
    for channel in range(2):
        intstr = str(bin(int(line[channel]))[2:].zfill(225))
        tmp = np.fromstring(intstr[::-1], np.int8) - 48
        tmp = tmp.reshape((15, 15))
        example[:, :, channel] = tmp.T
    x, y = axis(int(line[3]))
    example[x, y, 2] = 1.0

    examples = []
    policies = []
    values = []

    for k in range(4):
        tmp = np.zeros((15, 15, 3), dtype=np.float32)
        tmp[:] = np.rot90(example, k, (0, 1))
        rx, ry = axis(np.argmax(tmp[:, :, 2].T))
        policy = toind(rx, ry)
        tmp[:, :, 2] = int(line[2])
        examples.append(tmp)
        policies.append(policy)
        values.append(float(line[4]))
        if not augment:
            return examples, policies, values

    rev_example = example[::-1, :, :]
    for k in range(4):
        tmp = np.zeros((15, 15, 3), dtype=np.float32)
        tmp[:] = np.rot90(rev_example, k, (0, 1))
        rx, ry = axis(np.argmax(tmp[:, :, 2].T))
        policy = toind(rx, ry)
        tmp[:, :, 2] = int(line[2])
        examples.append(tmp)
        policies.append(policy)
        values.append(float(line[4]))
    return examples, policies, values


# @profile
def valid(black, white, x, y):
    """在x,y落子是否合法. 即此处无子
    """
    return (not black & gobit[(x, y)]) and (not white & gobit[(x, y)])


def posswap(t, black, white):
    if t % 2 == 0:
        return black, white
    else:
        return white, black


# @profile
def legal(black, white, t):
    """返回所有合法落子ind
    根据比赛规则：黑1必须天元，白1 3x3  黑2 5x5  白2没有限制"""
    stones = black | white
    if t == 0:
        legal_list = [toind(7, 7)]
    elif t == 1:
        legal_list = [
            toind(7 + i, 7 + j) for i in [-1, 0, 1] for j in [-1, 0, 1]
            if not gobit[(7 + i, 7 + j)] & stones
        ]
    elif t == 2:
        legal_list = [
            toind(7 + i, 7 + j)
            for i in [-2, -1, 0, 1, 2] for j in [-2, -1, 0, 1, 2]
            if not gobit[(7 + i, 7 + j)] & stones
        ]

    else:
        legal_list = [
            ind for ind in range(config.SIZE)
            if not (gobit[axis(ind)] & stones)
        ]
    return legal_list


def check(black, white, x, y, t):
    """check terminal.
    Args:
        black:  after action state
        white:  after action state
        x, y:   action axis
        t:      action time
    """
    mine, yours = posswap(t, black, white)
    row = mine & mask_row[x]
    col = mine & mask_col[y]
    zheng = mine & mask_zheng[x + y]
    fan = mine & mask_fan[14 - x + y]
    if any(i in complete5 for i in [row, col, zheng, fan]):
        return 1
    # 33 44 判负
    num3 = 0
    num4 = 0
    empty = ~(mine | yours)
    ind = toind(x, y)
    # cachedinfo mine empty nomine
    for case in [row, col, zheng, fan]:
        if case in open3:
            for info in open3[case]:
                if ind not in info[0]:
                    continue
                valid_e = all(gobit[axis(i)] & empty for i in info[1])
                valid_n = all(gobit[axis(i)] & mine == 0 for i in info[2])
                if valid_e and valid_n:
                    num3 += 1
                    break
        if case in open4:
            for info in open4[case]:
                if ind not in info[0]:
                    continue
                valid_e = all(gobit[axis(i)] & empty for i in info[1])
                valid_n = all(gobit[axis(i)] & mine == 0 for i in info[2])
                if valid_e and valid_n:
                    num4 += 1
                    break
    if ((num3 > 1) or (num4 > 1)) and (t % 2 == 0):
        return -1
    return 0


def show(black, white):
    """ plot board from binary int format.
    """
    for x in X:
        for y in Y:
            if (x == 7) and (y == 7):
                print("\033[%d;%d;%dm**\033[0m" % (0, 33, 41), end='')
            elif (black & gobit[(x, y)]):
                print("\033[%d;%d;%dm  \033[0m" % (0, 31, 41), end='')
            elif (white & gobit[(x, y)]):
                print("\033[%d;%d;%dm  \033[0m" % (0, 32, 42), end='')
            else:
                print("  ", end='')
        print("")


def show_np(mat):
    """ plot board from np.array format.
    """
    for x in range(15):
        for y in range(15):
            if (x == 7) and (y == 7):
                print("\033[%d;%d;%dm**\033[0m" % (0, 33, 41), end='')
            elif mat[x, y, 0] > 0:
                print("\033[%d;%d;%dm  \033[0m" % (0, 31, 41), end='')
            elif mat[x, y, 1] > 0:
                print("\033[%d;%d;%dm  \033[0m" % (0, 32, 42), end='')
            else:
                print("  ", end='')
        print("")


def show_pi(black, white, pi):

    pi = pi / sum(pi) * 100
    pi = pi.reshape((15, 15)).T
    max_ind = axis(np.argmax(pi))
    sx, sy = max_ind[1], max_ind[0]
    num_stone = 0
    for x in range(15):
        for y in range(15):
            if (black & gobit[(x, y)]) or (white & gobit[(x, y)]):
                num_stone += 1
    print(black, white, num_stone)
    if num_stone % 2 == 0:
        color = 41
    else:
        color = 42
    for x in range(15):
        for y in range(15):
            if (x == 7) and (y == 7):
                print("\033[%d;%d;%dm**\033[0m" % (0, 33, 41), end='')
            elif (black & gobit[(x, y)]):
                print("\033[%d;%d;%dm  \033[0m" % (0, 31, 41), end='')
            elif (white & gobit[(x, y)]):
                print("\033[%d;%d;%dm  \033[0m" % (0, 32, 42), end='')
            elif (x == sx) and (y == sy):
                print(
                    "\033[%d;%d;%dm%2d\033[0m" % (0, 37, color, int(pi[x, y])),
                    end='')
            elif int(pi[x, y]) >= 1:
                print("%2d" % int(pi[x, y]), end='')
            elif pi[x, y] > 0:
                print("--", end='')
            else:
                print("  ", end='')
        print("")


class Game():
    """五子棋环境 g = Game(black, white), 建成一个指定状态的Game类
    我在mac上测试每秒钟1500局左右
    现在统一用t代替bw，表示棋盘中子的个数，偶数该黑子下了

    add 是主要函数
    Args:
        x:  纵坐标，上面是0   好像和标准的不一样:(
        y:  横坐标，左边是0

    返回:
        'F':  非法
        'P':  什么都没发生
        'W':  白赢了
        'B':  黑赢了

    提供一个show() 函数，打印当前状态  x为黑， o为白
    """

    def __init__(self, t=1, black=gobit[(7, 7)], white=0):
        self.black = black
        self.white = white
        self.t = t
        self.logs = [(7, 7)]

    def newround(self, t=1, black=gobit[(7, 7)], white=0):
        self.black = black
        self.white = white
        self.t = t
        self.logs = [(7, 7)]

    def add(self, x, y):
        """落子"""
        if not valid(self.white, self.black, x, y):
            raise RuntimeError('duplicated move')
        self.logs.append((x, y))

        if self.t % 2 == 0:
            self.black += gobit[(x, y)]
        else:
            self.white += gobit[(x, y)]

        point = check(self.black, self.white, x, y, self.t)
        self.t += 1
        if point == 1:
            if self.t % 2 == 1:
                return "B"
            return "W"
        elif point == -1:
            return "J"
        else:
            return "P"

    def show(self):
        """TODO: 根据self.logs在终端可视化棋谱"""
        log = {}
        style = 0
        f_color = 0
        b_color = 0
        stupid = 0
        for index, (x, y) in enumerate(self.logs):
            log[(x, y)] = index
        # log = sorted(log, key=lambda x: (x[0], x[1]))
        print('--------show table--------')
        for i in range(15):
            for j in range(15):
                if (i, j) in log:
                    if (log[(i, j)] >= 100):
                        log[(i, j)] -= 100
                        stupid = 1
                    else:
                        stupid = 0
                    if (log[(i, j)] % 2 == 0):
                        b_color = 47
                        if stupid:
                            f_color = 31
                        else:
                            f_color = 30
                    else:
                        f_color = 37
                        if stupid:
                            b_color = 41
                        else:
                            b_color = 40
                    print(
                        "\033[%d;%d;%dm%02d\033[0m" % (style, f_color, b_color,
                                                       log[(i, j)]),
                        end='')
                else:
                    print("  ", end='')
            print("")
        print('--------------------------')


if __name__ == "__main__":

    g = Game(
        black=2923047876832840323968461801439717328221198352384,
        white=2923047876832840324602287101553832028969549955072,
        t=9)
    g.add(4, 8)
    show(g.black, g.white)
