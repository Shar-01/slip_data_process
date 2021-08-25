#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Sun Jun 27 15:48:18 2021

@author: deysh
"""

import pandas as pd
import numpy as np
import os
import pickle
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

def find_nearest_idx(arr, val, tol=1e-1):
    if np.min(np.abs(arr - val)) < tol:
        return np.argmin(np.abs(arr - val))
    else:
        return None

def get_slipfall_labels(annotation_indices, nb_samples, range_up_down=5):
    labels = np.array([1]* nb_samples)
    #indices = pd.read_csv(annotations_filename, sep="\t")
    for index in annotation_indices:
        labels[int(index)-range_up_down: 
            max(int(index)-range_up_down+1, int(index)+range_up_down)] = 0
    return labels

def get_slipfall_labels_uneven_range(annotation_indices, nb_samples, range_up_down=[-15, 5]):
    labels = np.array([1]* nb_samples)
    #indices = pd.read_csv(annotations_filename, sep="\t")
    for index in annotation_indices:
        labels[int(index)+range_up_down[0]: 
            max(int(index)+range_up_down[0]+1, int(index)+range_up_down[1])] = 0
    return labels

def get_indices_from_timestamps(timestamps, comparison_timestamps):
    indices = []
    for timestamp in timestamps:
        timestamp =  float(timestamp)
        near_time_idx = find_nearest_idx(comparison_timestamps, timestamp)
        print(timestamp, near_time_idx)
        if near_time_idx is not None:
            indices.append(near_time_idx)
    return indices

def get_joint_states(joint_states, n_dof=12, time_ranges=None):
    
    #joint_states = pd.read_csv(joint_state_filename)
    
    if time_ranges is not None:
        indices = [np.arange(ts[0], ts[1]) for ts in time_ranges]
        indices = np.concatenate(indices, axis=0)
    else:
        indices = np.arange(len(joint_states))
    timestamps = joint_states.rosbagTimestamp.values/1e9
    # get dof names
    arr_dof_names = np.array(
        [joint_states['name.'+str(i)].values[0]
         for i in range(n_dof)])
    # get joint positions
    arr_joint_positions = np.array(
        [joint_states['position.'+str(i)].values[indices]
         for i in range(n_dof)]).T
    # get joint velocities
    arr_joint_velocities = np.array(
        [joint_states['velocity.'+str(i)].values[indices] 
         for i in range(n_dof)]).T
    # get joint efforts
    arr_joint_efforts = np.array(
        [joint_states['effort.'+str(i)].values[indices] 
         for i in range(n_dof)]).T
    return (timestamps, arr_dof_names, arr_joint_positions, 
            arr_joint_velocities, arr_joint_efforts)

states_csv_folder = "/home/deysh/rosbag_analysis_pipeline/csvs/joint_states"
annotations_folder = "/home/deysh/rosbag_analysis_pipeline/csvs/Joint_states_annotations"
annotation_files = os.listdir(annotations_folder)

dict_joint_data = {}
for csv_file in os.listdir(states_csv_folder):
    print(csv_file)
    annotation_file = None
    for filename in annotation_files:
        if "_annot" in filename:
            bag_name = filename[:-4].rstrip("_annot")
        elif "_annotations" in filename:
            bag_name = filename[:-4].rstrip("_annotations")
        if bag_name in csv_file:
            annotation_file = filename
            break
    if annotation_file is None:
        print("No annotation file found, skipping")
        continue
    joint_state_filename = os.path.join(states_csv_folder, csv_file)
    df_joint_states = pd.read_csv(joint_state_filename)
    rosbag_timestamps = df_joint_states.rosbagTimestamp.values/1e9
    df_annotation_data = pd.read_csv(
            os.path.join(annotations_folder, annotation_file), '\t')
    annotation_timestamps = df_annotation_data["Bag Time"]
    slipfall_indices = get_indices_from_timestamps(
            annotation_timestamps, rosbag_timestamps)
    nb_total_samples = df_joint_states.shape[0]    
    slipfall_labels = get_slipfall_labels_uneven_range(slipfall_indices, nb_total_samples)
    df_joint_states["slipfall_label"] = slipfall_labels
    dict_joint_data[csv_file] = df_joint_states
    
    _, arr_dof_names, arr_joint_positions, arr_joint_velocities, arr_joint_efforts = get_joint_states(
            df_joint_states)
    fig, ax = plt.subplots()
    plot_timestamps = rosbag_timestamps - rosbag_timestamps[0]
    ax.plot(plot_timestamps, arr_joint_velocities)
    for index in slipfall_indices:
        ax.axvline(plot_timestamps[index], c='r')
        '''ax.axvspan(xmin = max(plot_timestamps[0], plot_timestamps[index-10]), 
                   xmax = min(plot_timestamps[index+10], plot_timestamps[-1]), 
                   alpha=0.5, color='r')'''
        print plot_timestamps[index]
    ax.set_title(csv_file)
    
# save as pickle
data_save_path = "../joint_states_data.pickle"
with open(data_save_path, 'wb') as handle:
    pickle.dump(dict_joint_data, handle, protocol=pickle.HIGHEST_PROTOCOL)
