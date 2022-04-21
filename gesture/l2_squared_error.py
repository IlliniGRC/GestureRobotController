import numpy as np
from pyquaternion import Quaternion
from itertools import combinations


def Qdis(Q1: Quaternion, Q2: Quaternion):
    return Quaternion.distance(Q1, Q2)


def l2_vector(Q_finger: dict):
    f = list()
    f.append(Quaternion(Q_finger['Thumb']))
    f.append(Quaternion(Q_finger['Index']))
    f.append(Quaternion(Q_finger['Middle']))
    f.append(Quaternion(Q_finger['Ring']))
    f.append(Quaternion(Q_finger['Little']))
    f.append(Quaternion(Q_finger['Hand']))
    l2_v = list()
    for a, b in combinations(f, 2):
        l2_v.append(Qdis(a, b))
    l2_v = np.array(l2_v)
    return l2_v


def l2_squared_error(curr_gesture: dict, gesture_data: dict, sensitivity):
    curr_vector = l2_vector(curr_gesture)
    predict_gesture = -1
    l2_min = np.inf
    for gesture_idx in gesture_data['dataset']:
        dataset_gesture = gesture_data['dataset'][gesture_idx]['Quaternion']
        dataset_vector = l2_vector(dataset_gesture)
        l2 = 0
        for element in range(len(curr_vector)):
            l2 += (curr_vector[element] - dataset_vector[element]) ** 2
        if l2 < l2_min:
            predict_gesture = gesture_idx
            l2_min = l2
        print(f'Gesture {gesture_idx} l2: {l2}')
    if l2_min > sensitivity:
        return 404
    return gesture_data['dataset'][predict_gesture]['tag']
