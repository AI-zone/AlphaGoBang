from env.gobang import gobit, axis, toind, mask_col, mask_row, mask_fan, show, mask_zheng
import itertools
from collections import defaultdict

# complete 5
complete5 = defaultdict(list)
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
                complete5[row_sum].append([(), ()])

tmp = list(complete5.keys())
show(tmp[21837], 0)
complete5[tmp[21837]]
