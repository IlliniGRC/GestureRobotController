from l2_squared_error import *

if __name__ == '__main__':
    data = np.array([[1, -1, 1], [1.4, -1, 1], [1, -1, 1], [1, -1, 1], [1, -1, 1], [1, -1, 1]])
    print(l2_squared_error(data, 0.5))
