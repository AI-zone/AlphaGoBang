from env.gobang import gobit, axis, toind, mask_col, mask_row, mask_fan, show, mask_zheng
import itertools
from collections import defaultdict
import random
import pickle
"""
判断依据。刚刚下完的人，自己形成了2个活3或者2个活4，则输.
这个程序用来缓存给check做判断.

"""
# complete 5
complete5 = defaultdict(list)
open4 = defaultdict(list)
open3 = defaultdict(list)

for x in range(15):
    # 一行最少要5个子， 最多只能13个子，否则长连
    for num_y in range(5, 14):
        possible_y = itertools.combinations(list(range(15)), num_y)
        for select_set in possible_y:
            row_sum = sum([gobit[x, i] for i in select_set])
            r = row_sum & mask_row[x]
            # why need row_sum & mask_row[x]
            have5 = r & (r << 15) & (r << 30) & (r << 45) & (r << 60)
            have6 = have5 & (r << 75)
            if (have5 > 0) and (have6 == 0):
                complete5[row_sum].append(([], [], []))

print("complete5")
for x in range(15):
    for num_y in range(5, 14):
        possible_y = itertools.combinations(list(range(15)), num_y)
        for select_set in possible_y:
            col_sum = sum([gobit[i, x] for i in select_set])
            c = col_sum & mask_col[x]
            have5 = c & (c << 1) & (c << 2) & (c << 3) & (c << 4)
            have6 = have5 & (c << 5)
            if (have5 > 0) and (have6 == 0):
                complete5[col_sum].append(([], [], []))

print("complete5")
for possible_num in range(5, 14):
    for num_y in range(5, possible_num):
        possible_y = itertools.combinations(list(range(possible_num)), num_y)
        for select_set in possible_y:
            fan_sum = sum(
                [gobit[i, 15 + i - possible_num] for i in select_set])
            f = fan_sum & mask_fan[possible_num]
            have5 = f & (f << 16) & (f << 32) & (f << 48) & (f << 64)
            have6 = have5 & (f << 80)
            if (have5 > 0) and (have6 == 0):
                complete5[fan_sum].append(([], [], []))

print("complete5")
for possible_num in range(5, 14):
    for num_y in range(5, possible_num):
        possible_y = itertools.combinations(list(range(possible_num)), num_y)
        for select_set in possible_y:
            zheng_sum = sum(
                [gobit[possible_num - 1 - i, i] for i in select_set])
            z = zheng_sum & mask_zheng[possible_num - 1]
            have5 = z & (z << 14) & (z << 28) & (z << 42) & (z << 56)
            have6 = have5 & (z << 70)
            if (have5 > 0) and (have6 == 0):
                complete5[zheng_sum].append(([], [], []))

print("complete5")
# 活三活四 注意棋盘边界的，要靠空白位置是否合法判断

# open 4 and open3
for x in range(15):
    # 一行最少要4个子， 最多只能12个子，否则长连
    for num_y in range(4, 13):
        possible_y = itertools.combinations(list(range(15)), num_y)
        for select_set in possible_y:
            row_sum = sum([gobit[x, i] for i in select_set])
            r = row_sum & mask_row[x]
            have5 = r & (r << 15) & (r << 30) & (r << 45) & (r << 60)
            if have5:
                # 需要不包含5
                continue
            have4 = r & (r << 15) & (r << 30) & (r << 45)
            if have4:
                # 找有哪4个子，以及周围的空白， 起始空白位置从0到9
                for begin in range(-1, 9):
                    # 注意，这里用的都是相对坐标（固定了x）
                    mine = [begin + i for i in range(2, 6)]
                    nomine = [
                        begin + i for i in [0, 7]
                        if (begin + i >= 0) and (begin + i <= 14)
                    ]
                    empty = [begin + 1, begin + 6]

                    valid_empty = all(i not in select_set for i in empty)
                    valid_mine = all(i in select_set for i in mine)
                    valid_nomine = all(i not in select_set for i in nomine)

                    if valid_empty and valid_mine and valid_nomine:
                        open4[row_sum].append(
                            ([toind(x, i)
                              for i in mine], [toind(x, i) for i in empty],
                             [toind(x, i) for i in nomine]))
                        # 找到了活4， 开始加活3
                        for remove in open4[row_sum][-1][0]:
                            # remove is ind
                            left_sum = row_sum - gobit[axis(remove)]
                            # 最后需要去重
                            new_s = open4[row_sum][-1][0][:]
                            new_s.remove(remove)
                            new_e = open4[row_sum][-1][1][:]
                            new_e.append(remove)
                            new_n = open4[row_sum][-1][2][:]
                            if (new_s, new_e) not in open3[left_sum]:
                                open3[left_sum].append((new_s, new_e, new_n))
print("complete5")
for x in range(15):
    for num_y in range(4, 13):
        possible_y = itertools.combinations(list(range(15)), num_y)
        for select_set in possible_y:
            col_sum = sum([gobit[i, x] for i in select_set])
            c = col_sum & mask_col[x]
            have5 = c & (c << 1) & (c << 2) & (c << 3) & (c << 4)
            if have5:
                continue
            have4 = c & (c << 1) & (c << 2) & (c << 3)
            if have4:
                for begin in range(-1, 9):
                    mine = [begin + i for i in range(2, 6)]
                    nomine = [
                        begin + i for i in [0, 7]
                        if (begin + i >= 0) and (begin + i <= 14)
                    ]
                    empty = [begin + 1, begin + 6]

                    valid_empty = all(i not in select_set for i in empty)
                    valid_mine = all(i in select_set for i in mine)
                    valid_nomine = all(i not in select_set for i in nomine)

                    if valid_empty and valid_mine and valid_nomine:
                        open4[col_sum].append(
                            ([toind(i, x)
                              for i in mine], [toind(i, x) for i in empty],
                             [toind(x, i) for i in nomine]))

                        for remove in open4[col_sum][-1][0]:
                            left_sum = col_sum - gobit[axis(remove)]
                            new_s = open4[col_sum][-1][0][:]
                            new_s.remove(remove)
                            new_e = open4[col_sum][-1][1][:]
                            new_e.append(remove)
                            new_n = open4[col_sum][-1][1][:]
                            if (new_s, new_e) not in open3[left_sum]:
                                open3[left_sum].append((new_s, new_e, new_n))
print("complete5")
# fan  line_id = 14+x-y

for line_id in range(5, 24):
    for num_y in range(6, 15):  # number of stones in a line
        max_stone_num = 15 - abs(14 - line_id)
        y_range = list(range(0, max_stone_num)) if line_id <= 14 else list(
            range(15 - max_stone_num, 15))
        # 线上的所有点
        line_points = [toind(line_id + y - 14, y) for y in y_range]
        subsets = itertools.combinations(line_points, num_y)
        for select_set in subsets:
            fan_sum = sum([gobit[axis(i)] for i in select_set])
            f = fan_sum & mask_fan[line_id]
            have5 = f & (f << 16) & (f << 32) & (f << 48) & (f << 64)
            if have5:
                continue
            have4 = f & (f << 16) & (f << 32) & (f << 48)
            if have4:
                # 用模式匹配， begin表示line 上起始点的y
                for begin in [y_range[0] - 1] + y_range:
                    if begin + 6 > 14:
                        continue
                    mine = [begin + i for i in [2, 3, 4, 5]]
                    nomine = [
                        begin + i for i in [0, 7]
                        if (begin + i >= 0) and (begin + i <= 14)
                    ]
                    empty = [begin + 1, begin + 6]

                    valid_empty = all(
                        toind(line_id + y - 14, y) not in select_set
                        for y in empty)
                    valid_mine = all(
                        toind(line_id + y - 14, y) in select_set for y in mine)
                    valid_nomine = all(
                        toind(line_id + y - 14, y) not in select_set
                        for y in nomine)

                    if valid_empty and valid_mine and valid_nomine:
                        open4[fan_sum].append(
                            ([toind(line_id + y - 14, y) for y in mine],
                             [toind(line_id + y - 14, y) for y in empty],
                             [toind(line_id + y - 14, y) for y in nomine]))
                        for remove in open4[fan_sum][-1][0]:
                            left_sum = fan_sum - gobit[axis(remove)]
                            new_s = open4[fan_sum][-1][0][:]
                            new_s.remove(remove)
                            new_e = open4[fan_sum][-1][1][:]
                            new_e.append(remove)
                            new_n = open4[fan_sum][-1][2][:]
                            if (new_s, new_e) not in open3[left_sum]:
                                open3[left_sum].append((new_s, new_e, new_n))
print("complete5")

# zheng line_id x+y
for line_id in range(5, 24):
    for num_y in range(6, 15):
        max_stone_num = 15 - abs(14 - line_id)
        y_range = list(range(0, max_stone_num)) if line_id <= 14 else list(
            range(15 - max_stone_num, 15))
        # 线上的所有点
        line_points = [toind(line_id - y, y) for y in y_range]
        subsets = itertools.combinations(line_points, num_y)

        for select_set in subsets:
            zheng_sum = sum([gobit[axis(i)] for i in select_set])
            z = zheng_sum & mask_zheng[line_id]
            have5 = z & (z << 14) & (z << 28) & (z << 42) & (z << 56)
            if have5:
                continue
            have4 = z & (z << 14) & (z << 28) & (z << 42)
            if have4:
                for begin in [y_range[0] - 1] + y_range:
                    if begin + 6 > 14:
                        continue
                mine = [begin + i for i in [2, 3, 4, 5]]
                nomine = [
                    begin + i for i in [0, 7]
                    if (begin + i >= 0) and (begin + i <= 14)
                ]
                empty = [begin + 1, begin + 6]

                valid_empty = all(
                    toind(line_id - y, y) not in select_set for y in empty)
                valid_mine = all(
                    toind(line_id - y, y) in select_set for y in mine)
                valid_nomine = all(
                    toind(line_id - y, y) not in select_set for y in nomine)

                if valid_empty and valid_mine and valid_nomine:
                    open4[zheng_sum].append(
                        ([toind(line_id - y, y) for y in mine],
                         [toind(line_id - y, y) for y in empty],
                         [toind(line_id - y, y) for y in nomine]))
                    for remove in open4[zheng_sum][-1][0]:
                        left_sum = zheng_sum - gobit[axis(remove)]
                        new_s = open4[zheng_sum][-1][0][:]
                        new_s.remove(remove)
                        new_e = open4[zheng_sum][-1][1][:]
                        new_e.append(remove)
                        new_n = open4[zheng_sum][-1][2][:]
                        if (new_s, new_e) not in open3[left_sum]:
                            open3[left_sum].append((new_s, new_e, new_n))
print("complete5")
tmp = list(open3.keys())
test_id = random.randrange(len(tmp))
show(tmp[test_id], 0)
print([axis(i) for i in open3[tmp[test_id]][0][0]],
      [axis(i) for i in open3[tmp[test_id]][0][1]],
      [axis(i) for i in open3[tmp[test_id]][0][2]])
len(tmp)
pickle.dump((complete5, open4, open3), open('./env/cached.pkl', 'wb'))
