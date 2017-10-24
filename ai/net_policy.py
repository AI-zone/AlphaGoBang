# @Author: chenyu
# @Date:   20_Oct_2017
# @Email:  yu.chen@pku.edu.cn
# @Filename: mcts.py
# @Last modified by:   chenyu
# @Last modified time: 20_Oct_2017
import os
import sys
used_gpu = sys.argv[1]
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = used_gpu

import tensorflow as tf
import numpy as np
import config

from ai.resnet import model_fn


def get_data(data_file_name):
    f = open(data_file_name).readlines()
    features = []
    labels = []
    values = []
    for line in f:
        if len(line) < 10:
            continue
        line = [int(i) for i in line.strip('\n').split(',')]
        example = np.zeros((15, 15, 2))
        for channel in range(2):
            tmp = np.fromstring('{0:0225b}'.format(line[channel]),
                                np.int8) - 48
            tmp = tmp.reshape((15, 15))
            example[:, :, channel] = tmp
        features.append(example)
        labels.append(line[2])
        values.append(line[3])
    return features, labels, values


def train_input_fn():
    data_file_name = '/data/gobang/warmup'
    features, labels, values = get_data(data_file_name)
    features = np.array(features)
    labels1 = np.array(labels)
    labels2 = np.array(values)
    return {'x': features}, {'policy': labels1, 'value': labels2}


if __name__ == "__main__":

    est_config = tf.estimator.RunConfig()
    est_config.replace(
        keep_checkpoint_max=1,
        save_checkpoints_steps=500,
        session_config=tf.ConfigProto(),
        save_checkpoints_secs=None,
        save_summary_steps=1000)
    params = dict(conv_filters=[256, 256, 256], learning_rate=0.001)
    classifier = tf.estimator.Estimator(
        model_fn=model_fn,
        params=params,
        model_dir="/tmp/test_resnet",
        config=est_config)

    classifier.train(input_fn=train_input_fn)
