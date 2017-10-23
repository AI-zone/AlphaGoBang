# @Author: chenyu
# @Date:   20_Oct_2017
# @Email:  yu.chen@pku.edu.cn
# @Filename: config.py
# @Last modified by:   chenyu
# @Last modified time: 21_Oct_2017

import multiprocessing

NUM_CPU = multiprocessing.cpu_count()

MODE = 1  # 1: pure self play  2: between AI
if NUM_CPU < 10:
    NUMPARALELL = 2
else:
    NUMPARALELL = 15

NUM_SIMULATIONS = 1600
TEMPERATURE = 1
EXPLORATION = 0.1
SIZE = 225
L = 20
GAMELENGTH = 30

PUNISH = -0.8  # for no result after L steps
DISTANCE = 1  # 0 mean no mask

LEARNINGRATE = 0.001
