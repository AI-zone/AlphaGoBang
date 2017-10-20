#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Aug  5 22:04:19 2017

@author: chenyu
"""

from __future__ import print_function


class Game():
    """五子棋环境 g = Game()  我在mac上测试每秒钟1500局左右

    add 是主要函数
    Args:
        who: "b" 表示黑 "w" 表示白
        x:  纵坐标，上面是0   好像和标准的不一样:(
        y:  横坐标，左边是0

    返回:
        'F':  非法
        'P':  什么都没发生
        'w':  白赢了
        'b':  黑赢了

    提供一个show() 函数，打印当前状态  x为黑， o为白
    """

    def __init__(self):
        self.black = 0
        self.white = 0

        self.X = [
            0x0, 0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8, 0x9, 0xa, 0xb, 0xc,
            0xd, 0xe
        ]
        self.Y = [
            0x0, 0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8, 0x9, 0xa, 0xb, 0xc,
            0xd, 0xe
        ]

        self.gobit = {}

        for x in self.X:
            for y in self.Y:
                self.gobit[(x, y)] = 2**(x + 15 * y)

        self.mask_col = [
            sum([self.gobit[(x, y)] for x in range(15)]) for y in range(15)
        ]
        self.mask_row = [
            sum([self.gobit[(x, y)] for y in range(15)]) for x in range(15)
        ]
        self.mask_zheng = [0] * 30
        self.mask_fan = [0] * 30
        for x in self.X:
            for y in self.Y:
                self.mask_zheng[x + y] += self.gobit[(x, y)]
                self.mask_fan[15 + x - y] += self.gobit[(x, y)]

    def newround(self):
        self.black = 0
        self.white = 0

    def add(self, who, x, y):

        if (self.black & self.gobit[(x, y)]) or (
                self.white & self.gobit[(x, y)]):
            return 'F'
        elif who == "b":
            self.black += self.gobit[(x, y)]
        elif who == "w":
            self.white += self.gobit[(x, y)]
        return self.check(who, x, y)

    def check(self, who, x, y):
        print(who, x, y)
        if who == 'b':
            board = self.black
        if who == 'w':
            board = self.white
        row = board & self.mask_row[x]
        col = board & self.mask_col[y]
        zheng = board & self.mask_zheng[x + y]
        fan = board & self.mask_fan[15 + x - y]
        if row & (row << 15) & (row << 30) & (row << 45) & (row << 60) > 0:
            return who.upper()
        if col & (col << 1) & (col << 2) & (col << 3) & (col << 4) > 0:
            return who.upper()
        if zheng & (zheng << 14) & (zheng << 28) & (zheng << 42) & (
                zheng << 56) > 0:
            return who.upper()
        if fan & (fan << 16) & (fan << 32) & (fan << 48) & (fan << 64) > 0:
            return who.upper()
        return "P"

    def show(self):
        s = ""
        for x in self.X:
            for y in self.Y:
                if (self.black & self.gobit[(x, y)]):
                    s += 'x'
                elif (self.white & self.gobit[(x, y)]):
                    s += 'o'
                else:
                    s += ' '
            s += '\n'
        print(s)


if __name__ == "__main__":
    g = Game()
    g.add('b', 7, 7)
    g.add('w', 8, 12)
    g.add('b', 7, 6)
    g.add('w', 6, 7)
    g.add('b', 6, 10)
    g.show()
    g.add('b', 7, 8)
    g.add('w', 7, 9)
    g.add('b', 7, 5)
    g.add('w', 4, 4)
    g.add('b', 7, 4)
    g.show()
