import numpy as np
from pyquaternion import Quaternion
from itertools import combinations


def Qdis(Q1: Quaternion, Q2: Quaternion):
    return Quaternion.sym_distance(Q1, Q2)


def l2_vector(Q_finger: dict):
    f = list()
    f.append(Quaternion(Q_finger['T']))
    f.append(Quaternion(Q_finger['I']))
    f.append(Quaternion(Q_finger['M']))
    f.append(Quaternion(Q_finger['R']))
    f.append(Quaternion(Q_finger['L']))
    f.append(Quaternion(Q_finger['H']))

    l2_v = list()
    for i in range(len(f)):
        for j in range(i):
            l2_v.append(Qdis(f[i], f[j]))
    return np.array(l2_v)


def l2_squared_error(curr_gesture: dict, database: dict, sensitivity):
    predict_gesture = -1
    l2_min = np.inf
    curr_vector = l2_vector(curr_gesture)
    for gesture_idx, gesture_quaternions in database.items():
        gesture_idx = int(gesture_idx)
        dataset_vector = l2_vector(gesture_quaternions)
        l2 = 0
        for element in range(len(curr_vector)):
            l2 += (curr_vector[element] - dataset_vector[element]) ** 2
        if l2 < l2_min:
            predict_gesture = gesture_idx
            l2_min = l2
        print(f'Gesture {gesture_idx} l2: {l2}')
    if l2_min > sensitivity:
        return 404
    return predict_gesture

def l2_squared_error_to_file(curr_gesture: dict, database: dict, sensitivity):
    to_ret = ""
    predict_gesture = -1
    l2_min = np.inf
    curr_vector = l2_vector(curr_gesture)
    for gesture_idx, gesture_quaternions in database.items():
        gesture_idx = int(gesture_idx)
        dataset_vector = l2_vector(gesture_quaternions)
        l2 = 0
        for element in range(len(curr_vector)):
            l2 += (curr_vector[element] - dataset_vector[element]) ** 2
        if l2 < l2_min:
            predict_gesture = gesture_idx
            l2_min = l2
        to_ret += f"{l2},"
    if l2_min > sensitivity:
        to_ret += f"-1\n"
    else:
        to_ret += f"{predict_gesture}\n"
    return to_ret
