"""
inference of network.
while True:
    addr, features = queue.get_all_or_a_batch()
    oracles = predict_fn(features)
    send_back(addr, oracles)
"""
# pylint: disable-msg=C0103
# pylint: disable-msg=E1129
import os
import sys
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
from env.gobang import int2array
msgpack_numpy.patch()


def call_saved_model():
    model_list = os.listdir('./models/')
    model_list.sort()
    best_model = './models/' + model_list[-1]
    policy_fn = predictor.from_saved_model(
        best_model, signature_def_key='predict/policy')
    value_fn = predictor.from_saved_model(
        best_model, signature_def_key='predict/value')
    return policy_fn, value_fn


class Runner():
    def __init__(self, policy_fn, value_fn):
        self.cache = {}
        self.policy_fn = policy_fn
        self.value_fn = value_fn

    def _buildsockets(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.ROUTER)
        self.socket.bind('ipc://./tmp/oracle_recv.ipc')

    def _continuous_recv(self):

        _addr, content = self.socket.recv_multipart()
        print(content)
        batch, identity = msgpack.loads(content)
        batch = [(int(i[0]), int(i[1])) for i in batch]
        features = []
        for each in batch:
            example = int2array(each)
            features.append(example)
        return features, identity

    def _reply(self, oracles, identities):
        for ind, identity in enumerate(identities):
            print(identity, oracles[ind])
            self.socket.send_multipart([identity, msgpack.dumps(oracles[ind])])

    def run(self):
        self._buildsockets()

        while True:
            features, identity = self._continuous_recv()
            p = self.policy_fn({'x': features})
            v = self.value_fn({'x': features})
            print(p)
            print(v)
            # self._reply((p, v), identity)


if __name__ == "__main__":
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.2)
    session_config = tf.ConfigProto(gpu_options=gpu_options)
    sess = tf.Session(config=session_config)
    with sess.as_default():
        policy_fn, value_fn = call_saved_model()
        runner = Runner(policy_fn, value_fn)

        runner.run()
