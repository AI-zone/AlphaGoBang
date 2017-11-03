# pylint: disable-msg=C0103
import os
import sys
import shutil
import names
used_gpu = sys.argv[1]
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = used_gpu

import tensorflow as tf
import numpy as np
import names
import config

from ai.net import model_fn
from env.gobang import show_np, axis, int2array


def get_data(data_file_name):
    f = open(data_file_name).readlines()
    duplicate = {}
    examples = []
    policies = []
    values = []
    for line in f:
        if len(line) < 3:
            continue
        line = line.strip('\n').split(',')
        if len(line) != 5:
            continue
        if abs(float(line[-1])) > 2:
            continue
        if (line[0], line[1], line[3]) in duplicate:
            # many state duplicated
            continue
        duplicate[(line[0], line[1], line[3])] = 0
        example, policy, value = int2array(line)
        examples += example
        policies += policy
        values += value
    return examples, policies, values


def my_numpy_input_fn(x,
                      y,
                      batch_size=128,
                      num_epochs=1,
                      shuffle=True,
                      queue_capacity=2000,
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
    data_file_name = '/data/gobang/dump_selfplay/00040004'
    features, labels, values = get_data(data_file_name)
    train_size = int(len(features) * 0.7)
    print('++++', train_size)
    afeatures = np.array(features[:train_size])
    alabels1 = np.array(labels[:train_size])
    alabels2 = np.array(values[:train_size])
    bfeatures = np.array(features[train_size:])
    blabels1 = np.array(labels[train_size:])
    blabels2 = np.array(values[train_size:])

    return {
        'x': afeatures
    }, {
        'policy': alabels1,
        'value': alabels2
    }, {
        'x': bfeatures
    }, {
        'policy': blabels1,
        'value': blabels2
    }


if __name__ == "__main__":
    train_x, train_y, test_x, test_y = load_data()
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.5)
    session_config = tf.ConfigProto(gpu_options=gpu_options)
    config = tf.estimator.RunConfig(session_config=session_config)

    train_input_fn = my_numpy_input_fn(train_x, train_y)
    test_input_fn = my_numpy_input_fn(test_x, test_y)
    params = dict(conv_filters=[32] * 12, learning_rate=0.001)
    classifier = tf.estimator.Estimator(
        model_fn=model_fn,
        params=params,
        model_dir="/data/gobang/models/test_resnet/",
        config=config)

    while True:
        try:
            classifier.train(input_fn=train_input_fn)
            classifier.evaluate(input_fn=test_input_fn)
        except KeyboardInterrupt:
            classifier.evaluate(input_fn=test_input_fn)
            save = input("USER interrupt, save? Y/N")
            if save == 'Y':
                features = {'x': tf.placeholder(tf.float32, [None, 15, 15, 3])}
                export_input_fn = tf.estimator.export.build_raw_serving_input_receiver_fn(
                    features)
                servable_model_dir = "/data/gobang/init"
                servable_model_path = classifier.export_savedmodel(
                    servable_model_dir, export_input_fn)
                ai_ver = os.listdir('/data/gobang/aipath')
                ai_name = names.get_last_name()
                while any(ai_name in i for i in ai_ver):
                    ai_name = names.get_last_name()
                shutil.move(servable_model_path,
                            '/data/gobang/aipath/%s-%04d' % (ai_name,
                                                             len(ai_ver) + 1))
            print("USER interrupt")
            break
