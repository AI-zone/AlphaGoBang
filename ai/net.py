# @Author: chenyu
# @Date:   19_Oct_2017
# @Email:  yu.chen@pku.edu.cn
# @Filename: resnet.py
# @Last modified by:   chenyu
# @Last modified time: 19_Oct_2017
"""Provides mnist_estimator function for generating tf.estimator.Estimators."""
import os
import config as hyper_config
import tensorflow as tf


def _resnet_logits(image, conv_filters, training):

    conv_initializer = tf.contrib.layers.xavier_initializer()
    x = image
    # 1 conv
    x = tf.layers.conv2d(
        x,
        filters=conv_filters[0],
        kernel_size=(3, 3),
        padding='SAME',
        activation=None,
        kernel_initializer=conv_initializer)
    x = tf.layers.batch_normalization(x, scale=False, training=training)
    x = tf.nn.relu(x)
    # many resnet block
    for n in conv_filters[1:]:
        inter = tf.layers.conv2d(
            x,
            filters=n,
            kernel_size=(3, 3),
            padding='SAME',
            activation=None,
            kernel_initializer=conv_initializer)
        inter = tf.layers.batch_normalization(
            inter, scale=False, training=training)
        inter = tf.nn.relu(inter)
        inter = tf.layers.conv2d(
            inter,
            filters=n,
            kernel_size=(3, 3),
            padding='SAME',
            activation=None,
            kernel_initializer=conv_initializer)
        inter = tf.layers.batch_normalization(
            inter, scale=False, training=training)
        inter = x + inter
        x = tf.nn.relu(inter)

    return x


def _bnconv_logits(image, conv_filters, training):

    x = image
    # 1 conv
    x = tf.layers.conv2d(
        x,
        filters=conv_filters[0],
        kernel_size=(5, 5),
        padding='SAME',
        activation=None)
    # x = tf.layers.batch_normalization(x, scale=False, training=training)
    x = tf.nn.relu(x)
    for n in conv_filters[1:]:
        x = tf.layers.conv2d(
            x, filters=n, kernel_size=(3, 3), padding='SAME', activation=None)
        # x = tf.layers.batch_normalization(x, scale=False, training=training)
        x = tf.nn.relu(x)
    return x


def model_fn(features, labels, mode, params, config):
    """bn version tower."""
    training = mode == tf.estimator.ModeKeys.TRAIN
    last_hidden_layer = _bnconv_logits(
        features['x'], params['conv_filters'], training=training)
    # policy head
    logits_head1 = tf.layers.conv2d(
        last_hidden_layer,
        filters=2,
        kernel_size=(1, 1),
        padding='SAME',
        activation=None)
    # logits_head1 = tf.layers.batch_normalization(
    #     logits_head1, scale=False, training=training)
    logits_head1 = tf.nn.relu(logits_head1)
    logits_head1 = tf.layers.flatten(logits_head1)
    logits_head1 = tf.layers.dense(logits_head1, 225, activation=None)
    pred = tf.argmax(logits_head1, axis=1)
    tf.summary.histogram('predict', pred)
    # value head
    logits_head2 = tf.layers.conv2d(
        last_hidden_layer,
        filters=1,
        kernel_size=(1, 1),
        padding='SAME',
        activation=None)
    # logits_head2 = tf.layers.batch_normalization(
    #     logits_head2, scale=False, training=training)
    logits_head2 = tf.nn.relu(logits_head2)
    logits_head2 = tf.layers.dense(logits_head2, 16, activation=tf.nn.relu)
    logits_head2 = tf.layers.flatten(logits_head2)
    logits_head2 = tf.layers.dense(logits_head2, 1, activation=tf.tanh)

    logits = {"policy": logits_head1, "value": logits_head2}
    head1 = tf.contrib.estimator.multi_class_head(n_classes=225, name="policy")
    head2 = tf.contrib.estimator.regression_head(name="value")
    head = tf.contrib.estimator.multi_head(
        [head1, head2], head_weights=[1.0, 1.0])

    probs = tf.nn.softmax(logits_head1) + 1e-6
    entropy = tf.reduce_mean(-tf.reduce_sum(probs * tf.log(probs), 1))

    def _train_op_fn(loss):
        loss += hyper_config.ENTROPY_REGUL * entropy  # add regularization
        optimizer = tf.train.AdamOptimizer(params['learning_rate'])
        # optimizer = tf.train.ProximalAdagradOptimizer(
        #     learning_rate=params['learning_rate'],
        #     l2_regularization_strength=0.2)
        return optimizer.minimize(loss, global_step=tf.train.get_global_step())

    return head.create_estimator_spec(
        features=features,
        labels=labels,
        mode=mode,
        train_op_fn=_train_op_fn,
        logits=logits)


if __name__ == "__main__":
    # test net
    pass
