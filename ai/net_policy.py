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
        example = np.zeros((15, 15, 2), dtype=np.float32)
        for channel in range(2):
            tmp = np.fromstring('{0:0225b}'.format(line[channel]),
                                np.int8) - 48
            tmp = tmp.reshape((15, 15))
            example[:, :, channel] = tmp
        features.append(example)
        labels.append(line[2])
        values.append(line[3])
    return features, labels, values


def my_numpy_input_fn(x,
                      y,
                      batch_size=128,
                      num_epochs=1,
                      shuffle=None,
                      queue_capacity=1000,
                      num_threads=1):
    """A numpy_input_fn for multi_head estimator.
        x: {'key': numpy arrray}
        y: {'head1': numpy array, 'head2': numpy array, ...}

    """
    import collections
    from tensorflow.python.estimator.inputs.queues import feeding_functions

    def input_fn():
        ordered_dict_x = collections.OrderedDict(
            sorted(x.items(), key=lambda t: t[0]))
        target_keys = []
        for tar_key in y:
            while tar_key in ordered_dict_x:
                tar_key += '_n'
            target_keys.append(tar_key)
            ordered_dict_x[tar_key] = y[tar_key]
        queue = feeding_functions._enqueue_data(  # pylint: disable=protected-access
            ordered_dict_x,
            queue_capacity,
            shuffle=shuffle,
            num_threads=num_threads,
            enqueue_size=batch_size,
            num_epochs=num_epochs)
        features = (queue.dequeue_many(batch_size)
                    if num_epochs is None else queue.dequeue_up_to(batch_size))

        if features:
            features.pop(0)
        features = dict(zip(ordered_dict_x.keys(), features))
        target = {}
        for tar_key in target_keys:
            target[tar_key] = features.pop(tar_key)
        return features, target

    return input_fn


def load_data():
    data_file_name = '/data/gobang/warmup'
    features, labels, values = get_data(data_file_name)
    features = np.array(features)
    labels1 = np.array(labels)
    labels2 = np.array(values)
    return {'x': features}, {'policy': labels1, 'value': labels2}


if __name__ == "__main__":
    x, y = load_data()
    train_input_fn = my_numpy_input_fn(x, y)
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
