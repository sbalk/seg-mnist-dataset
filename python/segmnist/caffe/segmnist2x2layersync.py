# imports
import json
import time
import pickle
import scipy.misc
import skimage.io
import caffe

import numpy as np
import os.path as osp

from xml.dom import minidom
from random import shuffle
from threading import Thread
from PIL import Image

from segmnist import SegMNIST


class SegMNIST2x2LayerSync(caffe.Layer):

    """
    This is a simple synchronous datalayer for training a network on the
    SegMNIST 2x2 dataset.
    """

    def setup(self, bottom, top):

        self.top_names = ['data', 'seg-label', 'cls-label']

        # === Read input parameters ===

        # params is a python dictionary with layer parameters.
        params = eval(self.param_str)

        # Check the parameters for validity.
        check_params(params)

        # store input as class variables
        self.batch_size = params['batch_size']

        # ex. mnist-training or mnist-validation
        self.mnist_dataset_name = params['mnist_dataset']

        # probability of the original background being masked
        self.prob_mask_bg = params['prob_mask_bg']

        # Create a batch loader to load the images.
        self.mnist = SegMNIST.load_standard_MNIST(self.mnist_dataset_name, shuffle=True)  # BatchLoader(params, None)
        self.batch_loader = SegMNIST(self.mnist, prob_mask_bg=self.prob_mask_bg)

        # === reshape tops ===
        # since we use a fixed input image size, we can shape the data layer
        # once. Else, we'd have to do it in the reshape call.
        top[0].reshape(
            self.batch_size, 1, params['im_shape'][0], params['im_shape'][1])
        # Note the 10 channels (for the 10 digits).
        top[1].reshape(self.batch_size, 10, 1, 1)
        if len(top) > 2:
            top[2].reshape(
                self.batch_size, 1, params['im_shape'][0], params['im_shape'][1])

        print_info("SegMNIST2x2LayerSync", params)

    def forward(self, bottom, top):
        """
        Load data.
        """
        (img_data, cls_label, seg_label) = self.batch_loader.create_batch(self.batch_size)
        top[0].data[...] = img_data
        top[1].data[...] = cls_label
        if len(top) > 2:
            top[2].data[...] = seg_label

    def reshape(self, bottom, top):
        """
        There is no need to reshape the data, since the input is of fixed size
        (rows and columns)
        """
        pass

    def backward(self, top, propagate_down, bottom):
        """
        These layers does not back propagate
        """
        pass


def check_params(params):
    """
    A utility function to check the parameters for the data layers.
    """
    assert 'mnist_dataset' in params.keys(
    ), 'Params must include mnist_dataset (mnist-training, mnist-validation).'

    required = ['batch_size', 'im_shape']
    for r in required:
        assert r in params.keys(), 'Params must include {}'.format(r)


def print_info(name, params):
    """
    Output some info regarding the class
    """
    print "{} initialized for dataset: {}, with bs: {}, im_shape: {}.".format(
        name,
        params['mnist_dataset'],
        params['batch_size'],
        params['im_shape'])