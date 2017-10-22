from env.gobang import gobit, axis, toind, mask_col, mask_row, mask_fan, show, mask_zheng
import itertools
from collections import defaultdict

import pickle
"""
判断依据。刚刚下完的人，自己形成了2个活3或者2个活4，则输

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
            have5 = r & (r << 15) & (r << 30) & (r << 45) & (r << 60)
            have6 = have5 & (r << 75)
            if (have5 > 0) and (have6 == 0):
                complete5[row_sum].append(([], []))

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
                for begin in range(0, 10):
                    # 注意，这里用的都是相对坐标（固定了x）
                    empty = [begin, begin + 5]
                    stones = [begin + i for i in range(1, 5)]
                    valid_empty = all(i not in select_set for i in empty)
                    valid_stone = all(i in select_set for i in stones)
                    if valid_empty and valid_stone:
                        open4[row_sum].append(([toind(x, i) for i in stones],
                                               [toind(x, i) for i in empty]))
                        # 找到了活4， 开始加活3

                        for remove in open4[row_sum][-1][0]:
                            # remove is ind
                            left_sum = row_sum - gobit[axis(remove)]
                            # 最后需要去重
                            new_s = open4[row_sum][-1][0][:]
                            new_s.remove(remove)
                            new_e = open4[row_sum][-1][1][:]
                            new_e.append(remove)
                            if (new_s, new_e) not in open3[left_sum]:
                                open3[left_sum].append((new_s, new_e))
tmp = list(open3.keys())
show(tmp[62110], 0)
print(open3[tmp[22314]])
len(tmp)
pickle.dump((complete5, open4, open3), open('./env/cached.pkl', 'wb'))
