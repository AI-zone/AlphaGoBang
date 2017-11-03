# @Author: chenyu
# @Date:   20_Oct_2017
# @Email:  yu.chen@pku.edu.cn
# @Filename: config.py
# @Last modified by:   chenyu
# @Last modified time: 21_Oct_2017

import multiprocessing
import names
import os
NUM_CPU = multiprocessing.cpu_count()

MODE = 1  # 1: pure self play  2: between AI
if NUM_CPU < 10:
    NUMPARALELL = 2
else:
    NUMPARALELL = 8

NUM_SIMULATIONS = 400
INFERENCE_BATCHSIZE = 256
GAMEPARALELL = 50
TEMPERATURE = 0.7
VISIT_WEIGHT = 1
UPDATE_DELAY = 0.25  # epsilon greedy in MCTS
SIZE = 225

L = 10
GAMELENGTH = 55
DISTANCE = 2  # 0 mean no mask
WHITE_ALLOWANCE = 0.5

LEARNINGRATE = 0.001
ENTROPY_REGUL = 0.01
VALUE_DECAY = 1
