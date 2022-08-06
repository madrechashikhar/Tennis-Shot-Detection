# -*- coding: utf-8 -*-
"""Deep Learning Project_LRCNN_Streamlit.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1tJPQMmWFwaNYiz__PuBLwUJdlLN7nNf8
"""
# Commented out IPython magic to ensure Python compatibility.
# %pip install streamlit
import streamlit as st
import cv2
from PIL import Image
import os

import tensorflow as tf
from tensorflow.keras.applications.inception_v3 import InceptionV3, preprocess_input
from tensorflow.keras.callbacks import TensorBoard, ModelCheckpoint, CSVLogger
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.models import Model, Sequential, load_model
from tensorflow.keras.layers import Input, LSTM, Dense, TimeDistributed, Lambda, Dropout, GRU
from tensorflow.keras import backend as K
from tensorflow.keras import regularizers
from data_utils_streamlit import DataSet

import numpy as np
import os
import os.path
import time

import argparse
import logging

# import seaborn as sns
import matplotlib.pyplot as plt
import pickle

def load_video():
    uploaded_video = st.file_uploader("Choose video", type=["mp4", "mov", "avi"])
    frame_skip = 5 # display every 5 frames

    if uploaded_video is not None: # run only when user uploads video
        vid = uploaded_video.name
        with open(vid, mode='wb') as f:
            f.write(uploaded_video.read()) # save video to disk

        st.markdown(f"""
        ### Files
        - {vid}
        """,
        unsafe_allow_html=True) # display file name

        vidcap = cv2.VideoCapture(vid) # load video from disk
        cur_frame = 0
        success = True

        while success:
            success, frame = vidcap.read() # get next frame from video
            if cur_frame % frame_skip == 0: # only analyze every n=300 frames
                print('frame: {}'.format(cur_frame)) 
                pil_img = Image.fromarray(np.array(frame)) # convert opencv frame (with type()==numpy) into PIL Image
                st.image(pil_img)
            cur_frame += 1
    return uploaded_video

# --- RNN MODEL --- #
def lstm(num_features=2048, hidden_units=256, dense_units=256, reg=1e-1, dropout_rate=1e-1, seq_length=16, num_classes=6):
	
	model = Sequential()
	
	model.add(Dropout(dropout_rate, input_shape=(seq_length, num_features)))  # input to LSTM
	model.add(LSTM(hidden_units, return_sequences=True))
	
	model.add(TimeDistributed(Dropout(dropout_rate)))

	model.add(TimeDistributed(Dense(num_classes, activation="softmax")))
	
	average_layer = Lambda(function=lambda x: K.mean(x, axis=1))
	model.add(average_layer)

	return model


def load_model():
    folder_path = '/Users/shrutigandhi/Documents/Deep_Learning_Project'
    sample_path = '/Users/shrutigandhi/Documents/Deep_Learning_Project/VIDEO_RGB_NEW/backhand/p32_bslice_s3'
    
    learning_rate= 1e-3 # 1e-4
    decay=0.0

    hidden_units = 128
    dense_units = 128
    reg = 0.0           # L2 regularization
    dropout_rate = 0.3  # dropout regularization
    batch_size = 128
    nb_epoch = 300 # 100


    # ---- OTHER PARAMETERS ---- #
    train_size = 0.8  # proportion of dataset that is training
    saved_model = None  # None, or pass in weights file
    # saved_model = "data/checkpoints/lstm_weights.0026-0.239.hdf5"

    num_classes = 6
    seq_length = 16    # essentially number of frames


    # --- LOAD DUMMY CNN MODEL --- #
    a = Input(shape=(1,))
    b = Dense(1)(a)
    model = Model(inputs=a, outputs=b)

    cnn_model = Model(inputs=a, outputs=b)


    # ------ EVALUATE MODEL ------ #
    # have to reinstantiate model to load weights properly
    rnn_model = lstm(hidden_units=hidden_units, dense_units=dense_units, 
                    reg=reg, dropout_rate=dropout_rate,
                    seq_length=seq_length, num_classes=num_classes)

    # setup optimizer: ADAM algorithm
    optimizer = Adam(lr=learning_rate, decay=decay)

    # metrics for judging performance of model
    metrics = ['categorical_accuracy'] # ['accuracy']  # if using 'top_k_categorical_accuracy', must specify k

    rnn_model.compile(loss='categorical_crossentropy', optimizer=optimizer,
        metrics=metrics)

    saved_weights = os.path.join(folder_path, 'lstm_weights.0300-0.743.hdf5')
    rnn_model.load_weights(saved_weights)

    # load and prepare test set
    video_file = load_video()
    sequence_path = '/Users/shrutigandhi/Documents/Deep_Learning_Project/sequences/backhand/p32_bslice_s3-16-features.npy'
    X_test = np.load(sequence_path)
    # sample = [None, 'backhand', 'p32_bslice_s3']

    dataset = DataSet(cnn_model)
    # dataset.get_fra
    X_train, Y_train = dataset.generate_data('train')
    X_train = tf.ragged.constant(X_train, ragged_rank=1)
    X_val, Y_val = dataset.generate_data('validation')
    X_test = np.expand_dims(X_test, axis=0)
    # X_test, Y_test = dataset.generate_data('test')
    # X_test = tf.ragged.constant(X_test, ragged_rank=1)

    Y_pred = rnn_model.predict(X_test)
    Y_pred_class = np.argmax(Y_pred,axis=1)


    target_names = ['backhand', 'bvolley', 'forehand', 'fvolley', 
                    'service', 'smash']

    return Y_pred_class[0] 


st.title('LRCNN model demo')
target_names = ['Backhand', 'Bvolley', 'Forehand', 'Fvolley',  'Service', 'Smash']
# result = st.button('Run on image')
# if result:
st.write('Calculating results...')
st.write(target_names[load_model()])