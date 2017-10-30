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
    policy_fn = predictor.from_saved_model(
        '/data/gobang/init/1509028062', signature_def_key='predict/policy')
    value_fn = predictor.from_saved_model(
        '/data/gobang/init/1509028062', signature_def_key='predict/value')
    return policy_fn, value_fn


class Runner():
    def __init__(self, policy_fn, value_fn):
        self.cache = {}
        self.queue = blist()
        self.policy_fn = policy_fn
        self.value_fn = value_fn
        self.identity = b'basic'

    def _build_recv_sockets(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.DEALER)
        self.socket.setsockopt(zmq.IDENTITY, self.identity)
        self.socket.connect('ipc://./tmp/oracle_recv.ipc')
        print("FINISH build socket")

    def _continuous_recv(self):
        self._build_recv_sockets()
        while True:
            print('start receiving')
            content = self.socket.recv()
            print(content)
            content, identity = msgpack.loads(content)
            example = np.zeros((15, 15, 2), dtype=np.float32)
            for channel in range(2):
                tmp = np.fromstring('{0:0225b}'.format(content[channel]),
                                    np.int8) - 48
                tmp = tmp.reshape((15, 15))
                example[:, :, channel] = tmp
                self.queue.append((example, identity))

    def _get_all_or_a_batch(self):
        while True:
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
        for ind, identity in enumerate(identities):
            print(identity, oracles[ind])
            self.socket.send_multipart([identity, msgpack.dumps(oracles[ind])])

    def run(self):

        thr = threading.Thread(target=self._continuous_recv)
        thr.start()

        while True:
            time.sleep(100)
            features, identities = self._get_all_or_a_batch()
            p = self.policy_fn({'x': features})
            v = self.value_fn({'x': features})
            self._reply((p, v), identities)


if __name__ == "__main__":
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.5)
    session_config = tf.ConfigProto(gpu_options=gpu_options)
    sess = tf.Session(config=session_config)
    with sess.as_default():
        policy_fn, value_fn = call_saved_model()
        runner = Runner(policy_fn, value_fn)

        runner.run()
