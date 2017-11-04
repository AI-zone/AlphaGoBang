"""Hyper params."""
# @Author: chenyu
# @Date:   20_Oct_2017
# @Email:  yu.chen@pku.edu.cn
# @Filename: config.py
# @Last modified by:   chenyu
# @Last modified time: 21_Oct_2017

import multiprocessing


def TEMPERATURE(t):
    """explore."""
    if t < 14:
        return 1
    return 0


NUM_CPU = multiprocessing.cpu_count()

MODE = 1  # 1: pure self play  2: between AI
if NUM_CPU < 10:
    NUMPARALELL = 2
else:
    NUMPARALELL = 8

NUM_SIMULATIONS = 400
REBORN = 50000
INFERENCE_BATCHSIZE = 256
GAMEPARALELL = 50

VISIT_WEIGHT = 0.05
UPDATE_DELAY = 0.01  # epsilon greedy in MCTS
SIZE = 225
ROOT_EXPLORE = 0.25
L = 8
GAMELENGTH = 35
DISTANCE = 1  # 0 mean no mask
WHITE_ALLOWANCE = 0.5

LEARNINGRATE = 0.001
ENTROPY_REGUL = 0.01
VALUE_DECAY = 1
