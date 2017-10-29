"""
inference of network.
while True:
    addr, features = queue.get_all_or_a_batch()
    oracles = predict_fn(features)
    send_back(addr, oracles)
"""

import os
import sys
import time
used_gpu = sys.argv[1]
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = used_gpu

import tensorflow as tf
import numpy as np
import threading
from tensorflow.contrib import predictor
import zmq
import msgpack
import msgpack_numpy
from blist import blist
msgpack_numpy.patch()


def call_saved_model():
    return predictor.from_saved_model('/data/gobang/init/1509028062')


class Predictor(object):
    def __init__(self, predict_fn):
        self.cache = {}
        self.queue = blist()
        self.predict_fn = predict_fn

    def _buildsockets(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.DEALER)
        self.socket.connect('ipc://./tmp/oracle')
        print("FINISH build socket")

    def _continuous_recv(self):
        while True:
            content = self.socket.recv()
            content, identity = msgpack.loads(content)
            example = np.zeros((15, 15, 2), dtype=np.float32)
            for channel in range(2):
                tmp = np.fromstring('{0:0225b}'.format(content[channel]),
                                    np.int8) - 48
                tmp = tmp.reshape((15, 15))
                example[:, :, channel] = tmp
                self.queue.append((example, identity))

    def _get_all_or_a_batch(self):
        if len(self.queue) > 256:
            batch_size = 256
        elif len(self.queue) == 0:
            time.sleep(0.01)
        else:
            batch_size = len(self.queue)
            feed_data = []
            identities = []
            for _ in range(batch_size):
                each_data = self.queue.pop(0)
                feed_data.append(each_data[0])
                identities.append(each_data[1])
            return feed_data, identities

    def _reply(self, oracles, identities):
        pass

    def start(self):
        self._buildsockets()
        thr = threading.Thread(target=self._continuous_recv)
        thr.start()

        while True:
            features, identities = self._get_all_or_a_batch()
            oracles = self.predict_fn({'x': features})
            self._reply(oracles, identities)


if __name__ == "__main__":
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.5)
    session_config = tf.ConfigProto(gpu_options=gpu_options)
    sess = tf.Session(config=session_config)
    with sess.as_default():
        predict_fn = call_saved_model()
        predictor = Predictor(predict_fn)
        predictor.strat()
