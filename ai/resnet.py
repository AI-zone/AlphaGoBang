# @Author: chenyu
# @Date:   19_Oct_2017
# @Email:  yu.chen@pku.edu.cn
# @Filename: resnet.py
# @Last modified by:   chenyu
# @Last modified time: 19_Oct_2017
"""Provides mnist_estimator function for generating tf.estimator.Estimators."""
import os
import config
import tensorflow as tf


def _get_logits(image, conv_filters, training):

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


def _get_confidences(self, logits):
    return tf.nn.softmax(logits)


def _get_loss(logits, labels):
    loss = tf.reduce_sum(
        tf.nn.sparse_softmax_cross_entropy_with_logits(
            labels=labels, logits=logits),
        name='loss')
    tf.summary.scalar('loss', loss)
    return loss


def _get_predictions(logits):
    return tf.argmax(logits, axis=-1)


def _get_accuracy(labels, predictions):
    acc1 = tf.metrics.mean(
        tf.nn.in_top_k(predictions=predictions, targets=labels, k=1))
    acc2 = tf.metrics.mean(
        tf.nn.in_top_k(predictions=predictions, targets=labels, k=2))
    tf.summary.scalar('acc1', acc1)
    tf.summary.scalar('acc2', acc2)
    return {'top1acc:': acc1, 'top2acc': acc2}


def model_fn(features, labels, mode, params, config):
    """bn version tower."""
    training = mode == tf.estimator.ModeKeys.TRAIN
    last_hidden_layer = _get_logits(
        features['x'], params['conv_filters'], training=training)
    print(last_hidden_layer.get_shape())
    # policy head
    logits_head1 = tf.layers.conv2d(
        last_hidden_layer,
        filters=2,
        kernel_size=(1, 1),
        padding='SAME',
        activation=None)
    logits_head1 = tf.layers.batch_normalization(
        logits_head1, scale=False, training=training)
    logits_head1 = tf.nn.relu(logits_head1)
    logits_head1 = tf.layers.flatten(logits_head1)
    logits_head1 = tf.layers.dense(logits_head1, 225, activation=None)

    # value head
    logits_head2 = tf.layers.conv2d(
        last_hidden_layer,
        filters=1,
        kernel_size=(1, 1),
        padding='SAME',
        activation=None)
    logits_head2 = tf.layers.batch_normalization(
        logits_head2, scale=False, training=training)
    logits_head2 = tf.nn.relu(logits_head2)
    logits_head2 = tf.layers.dense(logits_head2, 256, activation=tf.nn.relu)
    logits_head2 = tf.layers.flatten(logits_head2)
    logits_head2 = tf.layers.dense(logits_head2, 1, activation=tf.tanh)

    logits = {"policy": logits_head1, "value": logits_head2}
    # logits = logits_head2
    print(logits_head1.get_shape(), logits_head2.get_shape())
    head1 = tf.contrib.estimator.multi_class_head(n_classes=225, name="policy")
    head2 = tf.contrib.estimator.regression_head(name="value")
    head = tf.contrib.estimator.multi_head([head1, head2])

    def _train_op_fn(loss):
        optimizer = tf.train.AdamOptimizer(params['learning_rate'])
        return optimizer.minimize(loss, global_step=tf.train.get_global_step())

    return head.create_estimator_spec(
        features=features,
        labels=labels,
        mode=mode,
        train_op_fn=_train_op_fn,
        logits=logits)


if __name__ == "__main__":
    # test net
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
