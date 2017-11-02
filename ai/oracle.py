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
used_gpu = '0'
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = used_gpu

import tensorflow as tf
import numpy as np
import threading
import multiprocessing
from tensorflow.contrib import predictor
import zmq
import msgpack
import msgpack_numpy
from env.gobang import int2array
msgpack_numpy.patch()


def call_saved_model(model_path):
    policy_fn = predictor.from_saved_model(
        model_path, signature_def_key='predict/policy')
    value_fn = predictor.from_saved_model(
        model_path, signature_def_key='predict/value')
    return policy_fn, value_fn


class Runner():
    def __init__(self, policy_fn, value_fn, model_name):
        self.cache = {}
        self.policy_fn = policy_fn
        self.value_fn = value_fn
        self.model_name = model_name

    def _buildsockets(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.ROUTER)
        self.socket.bind('ipc://./tmp/oracle_%s' % self.model_name)
        print('receiving ', self.model_name)

    def _continuous_recv(self):
        """[mine, yours, color]"""
        _addr, content = self.socket.recv_multipart()
        batch, identity = msgpack.loads(content)
        batch = [(int(i[0]), int(i[1]), int(i[2])) for i in batch]
        features = []
        for each in batch:
            example = int2array(each, False)
            features.append(example)
        return features, identity

    def _reply(self, oracles, identity):
        self.socket.send_multipart(
            [bytes(identity, 'utf-8'),
             msgpack.dumps(oracles)])

    def run(self):
        """recv from player and sess.run"""
        self._buildsockets()
        while True:
            features, identity = self._continuous_recv()
            p = self.policy_fn({'x': features})
            v = self.value_fn({'x': features})
            self._reply((p['probabilities'], v['predictions']), identity)


def start_ai(model_name):
    model_path = '/data/gobang/aipath/' + model_name
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=0.2)
    session_config = tf.ConfigProto(gpu_options=gpu_options)
    sess = tf.Session(config=session_config)
    with sess.as_default():
        policy_fn, value_fn = call_saved_model(model_path)
        runner = Runner(policy_fn, value_fn, model_name)
        runner.run()


if __name__ == "__main__":
    ai_process = multiprocessing.Process(
        target=start_ai, args=('Petrillo-0001', ))
    ai_process.start()
    ai_process.join()
