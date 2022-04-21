import argparse
import json
import time
import numpy as np
from serial import Serial
from l2_squared_error import l2_squared_error
from pyquaternion import Quaternion

esp32Port = 5
robotPort = 2


def Q2Euler(Q: Quaternion):
    qw, qx, qy, qz = Q.elements
    sinr_cosp = 2 * (qw * qx + qy * qz)
    cosr_cosp = 1 - 2 * (qx * qx + qy * qy)
    roll = np.arctan2(sinr_cosp, cosr_cosp)

    sinp = 2 * (qw * qy - qz * qx)
    if np.abs(sinp) >= 1:
        pitch = np.copysign(np.pi / 2, sinp)
    else:
        pitch = np.arcsin(sinp)

    siny_cosp = 2 * (qw * qz + qx * qy)
    cosy_cosp = 1 - 2 * (qy * qy + qz * qz)
    yaw = np.arctan2(siny_cosp, cosy_cosp)

    return np.array([roll, pitch, yaw])


def main(args):
    Q_list = dict()
    QT = list()
    QI = list()
    QM = list()
    QR = list()
    QL = list()
    QH = list()
    port = Serial(f'/dev/pts/{esp32Port}')
    robot = Serial(f'/dev/pts/{robotPort}')
    print('Opening esp32: ' + port.name)
    print('Opening robot: ' + robot.name)
    count = 0
    init_z = 0
    flag_init = True
    while True:
        count += 1
        port.flush()
        robot.flush()
        report = port.read_until(expected=b"\r\n")
        if len(report) % 15 != 2:
            continue
        index = 0
        while index < len(report) - 2:
            identifier, quaternions, accelerometers = report[index:index + 1], report[index + 1:index + 9], report[
                                                                                                            index + 9:index + 15]
            index += 15
            q0 = np.short(quaternions[1] << 8 | quaternions[0]) / 32768
            q1 = np.short(quaternions[3] << 8 | quaternions[2]) / 32768
            q2 = np.short(quaternions[5] << 8 | quaternions[4]) / 32768
            q3 = np.short(quaternions[7] << 8 | quaternions[6]) / 32768
            Q = list(np.array([q0, q1, q2, q3]))
            if identifier == b'T':  # Thumb
                QT = Q
            elif identifier == b'I':  # Index
                QI = Q
            elif identifier == b'M':  # Middle
                QM = Q
            elif identifier == b'R':  # Ring
                QR = Q
            elif identifier == b'L':  # Little
                QL = Q
            elif identifier == b'H':  # Hand
                QH = Q
        Q_list['Thumb'] = QT
        Q_list['Index'] = QI
        Q_list['Middle'] = QM
        Q_list['Ring'] = QR
        Q_list['Little'] = QL
        Q_list['Hand'] = QH
        if args.method == 'neural':
            print('use neural')
        elif args.method == 'l2' and count % 7 == 0:
            with open('gesture_l2.json', 'r') as f:
                content = json.load(f)
            gesture = l2_squared_error(Q_list, content, 5)
            print(f'\nPrediction: {gesture}')
            if gesture == 0:
                angle = Q2Euler(Quaternion(QH))
                flag_init = False
                init_z = angle[2]
                robot.write(b'hld|')
            if not flag_init and gesture == 1:
                angle = Q2Euler(Quaternion(QH))
                z_move = angle[2] - init_z
                # print(angle / np.pi * 180)
                if abs(angle[1] * 100) < 15:
                    angle[1] = 0
                if abs(angle[0] * 150) < 20:
                    angle[0] = 0
                if abs(z_move * 100) < 25:
                    z_move = 0
                buffer = f'chs|{int(-angle[1] * 100)},{int(angle[0] * 150)},{int(-z_move * 100)}'
                # print(buffer)
                robot.write(str.encode(buffer))
            print(u'{}[2J{}[;H'.format(chr(27), chr(27)), end='')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ECE 445 Project')
    parser.add_argument('--method', type=str, default='l2', help='gesture recognition method, [l2]')
    args = parser.parse_args()
    main(args)
