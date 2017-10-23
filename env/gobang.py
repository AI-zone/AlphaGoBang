#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug  5 22:04:19 2017

@author: chenyu
"""

import config
import pickle

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


# @profile
def valid(black, white, x, y):
    """在x,y落子是否合法. 即此处无子
    """
    return (not black & gobit[(x, y)]) and (not white & gobit[(x, y)])


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
    # elif t <= 10:
    #     legal_list = [
    #         toind(7 + i, 7 + j) for i in range(-4, 5) for j in range(-4, 5)
    #         if not gobit[(7 + i, 7 + j)] & stones
    #     ]
    else:
        legal_list = [
            ind for ind in range(config.SIZE) if not gobit[axis(ind)] & stones
        ]
    # empty = []
    # for ind in legal_list:
    #     if valid(black, white, *axis(ind)):
    #         empty.append(ind)
    return legal_list


# @profile
def check_backup(board, x, y):
    """检查刚刚落子的那个人是否赢了"""
    row = board & mask_row[x]
    col = board & mask_col[y]
    zheng = board & mask_zheng[x + y]
    fan = board & mask_fan[14 - x + y]
    if row & (row << 15) & (row << 30) & (row << 45) & (row << 60) > 0:
        return True
    if col & (col << 1) & (col << 2) & (col << 3) & (col << 4) > 0:
        return True
    if zheng & (zheng << 14) & (zheng << 28) & (zheng << 42) & (
            zheng << 56) > 0:
        return True
    if fan & (fan << 16) & (fan << 32) & (fan << 48) & (fan << 64) > 0:
        return True


def check(mine, yours, x, y):
    """检查刚刚落子的那个人(棋盘mine)是否赢+1，是否33，44禁手-1，其他0.
    !!!check里面不区分黑白
    """
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
    if (num3 > 1) or (num4 > 1):
        return -1
    return 0


def show(black, white):
    """TODO: 根据self.logs改成可视化棋谱，类似AlphaGo围棋SGF图片"""
    for x in X:
        for y in Y:
            if (black & gobit[(x, y)]):
                print("\033[%d;%d;%dm  \033[0m" % (0, 31, 41), end='')
            elif (white & gobit[(x, y)]):
                print("\033[%d;%d;%dm  \033[0m" % (0, 32, 42), end='')
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

    def __init__(self, t=0, black=0, white=0):
        self.black = black
        self.white = white
        self.t = t
        self.logs = []

    def newround(self, t=0, black=0, white=0):
        self.black = black
        self.white = white
        self.t = t
        self.logs = []

    def add(self, x, y):
        """落子"""
        if not valid(self.white, self.black, x, y):
            raise RuntimeError('duplicated move')
        self.logs.append((x, y))
        if self.t % 2 == 0:
            self.black += gobit[(x, y)]
            self.t += 1
            point = check(self.black, self.white, x, y)
            if point == 1:
                return "B"
            elif point == -1:
                return "J"
            else:
                return "P"
        else:
            self.white += gobit[(x, y)]
            self.t += 1
            point = check(self.white, self.black, x, y)
            if point == 1:
                return "W"
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

    g = Game()
    g.add(7, 7)
    g.add(3, 7)
    g.add(7, 8)
    g.add(3, 8)
    g.add(5, 7)
    g.add(1, 7)
    g.add(6, 8)
    g.add(2, 8)
    g.add(7, 9)

    g.add(3, 9)
    g.add(8, 10)
    g.add(3, 10)
    g.add(9, 11)
    g.add(3, 11)
    g.show()
    yours = g.white
    mine = g.black
    x, y = 7, 9
