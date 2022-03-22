import numpy as np

gesture_database = [
    ("test gesture 1", np.array([[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]])),
    ("test gesture 2", np.array([[0, 0, 0], [1, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]))
]


def l2_squared_error(imu_data, sensitivity):
    gesture_imu = np.array(imu_data)
    for i in range(1, 6):
        for j in range(3):
            gesture_imu[i][j] -= imu_data[0][j]

    l2_array = list()
    for gesture_data in gesture_database:
        l2 = 0
        for i in range(1, 6):
            for j in range(3):
                l2 += (gesture_imu[i][j] - gesture_data[1][i][j]) ** 2
        l2_array.append(l2)

    idx = np.argmin(np.array(l2_array))
    if l2_array[idx] < sensitivity:
        gesture = gesture_database[idx][0]
    else:
        gesture = "404"
    return gesture
