# pylint: disable-msg=C0103
# pylint: disable-msg=W0621
# pylint: disable-msg=E1101
# pylint: disable-msg=E0632
"""
Created on Sat Aug  5 22:04:19 2017

@author: chenyu
"""
import pickle
import config
import numpy as np

try:
    complete5, complete6, open4, open3 = pickle.load(
        open('./env/cached.pkl', 'rb'))
except:  # pylint: disable-msg=W0702
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
    """0-224 ind to axis (x, y)"""
    return ind % 15, ind // 15


def toind(x, y):
    """axis(x, y) to 0-224 ind"""
    return x + 15 * y


def int2array(line, train=True):
    """Helper function to generate features, policies and values.
    Args:
        line: [mine, yours, color, action, value] for train
              [mine, yours, color] for evaluate
    return: examples, policies, values list of augmentations for train
            one signle example 3d-array for evaluate

    """
    example = np.zeros((15, 15, 3), dtype=np.float32)
    for channel in range(2):
        intstr = str(bin(int(line[channel]))[2:].zfill(225))
        tmp = np.fromstring(intstr[::-1], np.int8) - 48
        tmp = tmp.reshape((15, 15))
        example[:, :, channel] = tmp.T
    if train:
        example[axis(int(line[3]))[0], axis(int(line[3]))[1], 2] = 1.0
    else:
        example[:, :, 2] = int(line[2])
        return example

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
    """True if empty else False
    """
    return (not black & gobit[(x, y)]) and (not white & gobit[(x, y)])


def posswap(t, black, white):
    """Helper function that generates (mine, yours) board"""
    if t % 2 == 0:
        return black, white
    return white, black


# @profile
def legal(black, white, t):
    """Return valid moves list."""
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


def check(black, white, x, y, t):  # pylint: disable-msg=R0914
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
    if any(i in complete6 for i in [row, col, zheng, fan]):
        return -1
    if any(i in complete5 for i in [row, col, zheng, fan]):
        return 1
    # 33 44
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
            elif black & gobit[(x, y)]:
                print("\033[%d;%d;%dm  \033[0m" % (0, 31, 41), end='')
            elif white & gobit[(x, y)]:
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


def show_pi(black, white, pi, p, values, Q):  # pylint: disable-msg=R0912
    """Plot the policy pi, along with board.
    Args:
        black, white: binary board int.
        pi: numpy array of length 225.
    """
    pi = pi / sum(pi) * 100
    pi = pi.reshape((15, 15)).T
    p = p / sum(p) * 100
    p = p.reshape((15, 15)).T
    values = values * 100
    values = np.clip(values, -99, 99)
    values = values.reshape((15, 15)).T
    Q = Q * 100
    Q = np.clip(Q, -99, 99)
    Q = Q.reshape((15, 15)).T
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
            elif black & gobit[(x, y)]:
                print("\033[%d;%d;%dm  \033[0m" % (0, 31, 41), end='')
            elif white & gobit[(x, y)]:
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
        print("    ", end='')
        for y in range(15):
            if (x == 7) and (y == 7):
                print("\033[%d;%d;%dm**\033[0m" % (0, 33, 41), end='')
            elif black & gobit[(x, y)]:
                print("\033[%d;%d;%dm  \033[0m" % (0, 31, 41), end='')
            elif white & gobit[(x, y)]:
                print("\033[%d;%d;%dm  \033[0m" % (0, 32, 42), end='')
            elif int(p[x, y]) >= 1:
                print("%2d" % int(p[x, y]), end='')
            elif p[x, y] > 0.005:
                print("--", end='')
            else:
                print("  ", end='')
        print("    ", end='')
        for y in range(15):
            if (x == 7) and (y == 7):
                print("\033[%d;%d;%dm**\033[0m" % (0, 33, 41), end='')
            elif black & gobit[(x, y)]:
                print("\033[%d;%d;%dm  \033[0m" % (0, 31, 41), end='')
            elif white & gobit[(x, y)]:
                print("\033[%d;%d;%dm  \033[0m" % (0, 32, 42), end='')
            elif values[x, y] > 0.1:
                print(
                    "\033[%d;%d;%dm%2d\033[0m" % (0, 33, 40,
                                                  int(values[x, y])),
                    end='')
            elif values[x, y] < -0.1:
                print(
                    "\033[%d;%d;%dm%2d\033[0m" % (0, 34, 40,
                                                  int(-values[x, y])),
                    end='')
            else:
                print("  ", end='')
        print("    ", end='')
        for y in range(15):
            if (x == 7) and (y == 7):
                print("\033[%d;%d;%dm**\033[0m" % (0, 33, 41), end='')
            elif black & gobit[(x, y)]:
                print("\033[%d;%d;%dm  \033[0m" % (0, 31, 41), end='')
            elif white & gobit[(x, y)]:
                print("\033[%d;%d;%dm  \033[0m" % (0, 32, 42), end='')
            elif Q[x, y] > 0.1:
                print(
                    "\033[%d;%d;%dm%2d\033[0m" % (0, 33, 40, int(Q[x, y])),
                    end='')
            elif Q[x, y] < -0.1:
                print(
                    "\033[%d;%d;%dm%2d\033[0m" % (0, 34, 40, int(-Q[x, y])),
                    end='')
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
    """

    def __init__(self, t=1, black=gobit[(7, 7)], white=0):
        self.black = black
        self.white = white
        self.t = t
        self.logs = [(7, 7)]

    def newround(self, t=1, black=gobit[(7, 7)], white=0):
        """Start a new game"""
        self.black = black
        self.white = white
        self.t = t
        self.logs = [(7, 7)]

    def add(self, x, y):
        """Move
        Return:
            'F':  False
            'P':  go on
            'W':  white  win
            'B':  black win
            'J':  ban
        """
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

    def show(self):  # pylint: disable-msg=R0912
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
                    if log[(i, j)] >= 100:
                        log[(i, j)] -= 100
                        stupid = 1
                    else:
                        stupid = 0
                    if log[(i, j)] % 2 == 0:
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
