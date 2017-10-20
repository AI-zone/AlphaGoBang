# @Author: chenyu
# @Date:   19_Oct_2017
# @Email:  yu.chen@pku.edu.cn
# @Filename: resnet.py
# @Last modified by:   chenyu
# @Last modified time: 19_Oct_2017
"""Provides mnist_estimator function for generating tf.estimator.Estimators."""
import os
import tensorflow as tf


def _get_logits(image, conv_filters, dense_nodes, n_classes, training):

    conv_initializer = tf.contrib.layers.xavier_initializer()
    fc_initializer = tf.contrib.layers.xavier_initializer()
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

    # 2-head output, head1 for policy
    x1 = tf.layers.conv2d(
        x,
        filters=2,
        kernel_size=(1, 1),
        padding='SAME',
        activation=None,
        kernel_initializer=conv_initializer)
    x1 = tf.layers.batch_normalization(x1, scale=False, training=training)
    x1 = tf.nn.relu(x1)

    x1 = tf.contrib.layers.flatten(x1)
    head1 = tf.layers.dense(
        x1, 225, activation=tf.nn.relu, kernel_initializer=fc_initializer)

    # 2-head output, head1 for value

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


def _get_train_op(loss, learning_rate):
    optimizer = tf.train.AdamOptimizer(learning_rate)
    steps = tf.get_collection(tf.GraphKeys.GLOBAL_STEP)
    if len(steps) == 1:
        step = steps[0]
    else:
        raise Exception('Multiple global steps disallowed')
    update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
    with tf.control_dependencies(update_ops):
        train_op = optimizer.minimize(loss, step)
    return train_op


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
    logits = _get_logits(
        features['x'],
        params['conv_filters'],
        params['dense_nodes'],
        params['n_classes'],
        training=training)
    predictions = _get_predictions(logits)
    export_outputs = {
        'forecast': tf.estimator.export.PredictOutput({
            'probs': logits
        })
    }
    if training:
        loss = _get_loss(logits, labels)
        train_op = _get_train_op(loss, params['learning_rate'])
        return tf.estimator.EstimatorSpec(
            mode=mode,
            loss=loss,
            train_op=train_op,
            export_outputs=export_outputs)
    elif mode == tf.estimator.ModeKeys.EVAL:
        loss = _get_loss(logits, labels)

        eval_metric_ops = _get_accuracy(labels, logits)
        return tf.estimator.EstimatorSpec(
            mode=mode,
            loss=loss,
            eval_metric_ops=eval_metric_ops,
            export_outputs=export_outputs)
    elif mode == tf.estimator.ModeKeys.PREDICT:
        return tf.estimator.EstimatorSpec(
            mode=mode, predictions=predictions, export_outputs=export_outputs)
    else:
        raise Exception('mode unrecognized: %s' % mode)
