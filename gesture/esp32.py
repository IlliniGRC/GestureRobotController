import numpy as np
from pyquaternion import Quaternion
from serial import Serial
import keyboard
import json


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


def quaternion_rotation_matrix(Q: Quaternion):
    a, b, c, d = Q.elements
    r00 = 2 * a ** 2 - 1 + 2 * b ** 2
    r01 = 2 * b * c + 2 * a * d
    r02 = 2 * b * d - 2 * a * c
    r10 = 2 * b * c - 2 * a * d
    r11 = 2 * a ** 2 - 1 + 2 * c ** 2
    r12 = 2 * c * d + 2 * a * b
    r20 = 2 * b * d + 2 * a * c
    r21 = 2 * c * d - 2 * a * b
    r22 = 2 * a ** 2 - 1 + 2 * d ** 2
    rot_matrix = np.array([[r00, r01, r02],
                           [r10, r11, r12],
                           [r20, r21, r22]])
    return rot_matrix


def Qdis(Q1: Quaternion, Q2: Quaternion):
    return Quaternion.distance(Q1, Q2)


def display(port):
    g = 9.8

    QT = Quaternion()
    QI = Quaternion()
    QM = Quaternion()
    QR = Quaternion()
    QL = Quaternion()
    QH = Quaternion()
    # QA = Quaternion()

    while True:
        report = port.read_until(expected=b"\r\n")
        # os.system('clear')
        print(u'{}[2J{}[;H'.format(chr(27), chr(27)), end='')
        if len(report) % 15 != 2:
            continue
        index = 0
        to_report = ''
        while index < len(report) - 2:
            identifier, quaternions, accelerometers = report[index:index + 1], report[index + 1:index + 9], report[index + 9:index + 15]
            index += 15
            q0 = np.short(quaternions[1] << 8 | quaternions[0]) / 32768
            q1 = np.short(quaternions[3] << 8 | quaternions[2]) / 32768
            q2 = np.short(quaternions[5] << 8 | quaternions[4]) / 32768
            q3 = np.short(quaternions[7] << 8 | quaternions[6]) / 32768
            Q = Quaternion([q0, q1, q2, q3])
            ax = np.short((accelerometers[1]) << 8 | accelerometers[0]) / 32768 * 16 * g
            ay = np.short((accelerometers[3]) << 8 | accelerometers[2]) / 32768 * 16 * g
            az = np.short((accelerometers[5]) << 8 | accelerometers[4]) / 32768 * 16 * g

            roll, pitch, yaw = Q2Euler(Q) / np.pi * 180

            if identifier == b'T':  # Thumb
                to_report += 'Thumb '
                QT = Q
            elif identifier == b'I':  # Index
                to_report += 'Index '
                QI = Q
            elif identifier == b'M':  # Middle
                to_report += 'Middle'
                QM = Q
            elif identifier == b'R':  # Ring
                to_report += 'Ring  '
                QR = Q
            elif identifier == b'L':  # Little
                to_report += 'Little'
                QL = Q
            elif identifier == b'H':  # Hand
                to_report += 'Hand  '
                QH = Q
            # elif identifier == b'A':  # Arm
            #     to_report += "Arm   "
            #     QA = Q
            to_report += f'| roll:{roll:8.3f}, pitch:{pitch:8.3f}, yaw:{yaw:8.3f}. Q0:{q0:8.3f}, Q1:{q1:8.3f}, Q2:{q2:8.3f}, Q3:{q3:8.3f}, AX:{ax:8.3f}, AY:{ay:8.3f}, AZ:{az:8.3f}\n'
        print(to_report)
        if keyboard.is_pressed('q'):
            break


def collect(port, mode):
    if mode == 'Mode 1':
        file_name = 'dataset.json'
    elif mode == 'Mode 2':
        file_name = 'gesture_l2.json'
    else:
        print('Mode Error!')
        return
    try:
        with open(file_name, 'r') as f:
            content = json.load(f)
    except Exception:
        content = dict()
    with open(file_name, 'w') as f:
        if 'frame_count' not in content:
            content['frame_count'] = 0
        frame_count = content['frame_count']
        QT = list()
        QI = list()
        QM = list()
        QR = list()
        QL = list()
        QH = list()
        # QA = list()

        flag = False

        while True:
            idx = input(f'Gesture idx: ')
            if idx == '' or idx[-1] == 'q':
                break
            idx = int(idx[-1])
            num = 0
            while True:
                report = port.read_until(expected=b"\r\n")
                if keyboard.is_pressed('space'):
                    if flag:
                        continue
                    flag = True
                    if len(report) % 15 != 2:
                        continue
                    index = 0
                    while index < len(report) - 2:
                        identifier, quaternions, accelerometers = report[index:index + 1], report[
                                                                                           index + 1:index + 9], report[
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
                        # elif identifier == b'A':  # Arm
                        #     QA = Q
                    Q_list = dict()
                    Q_list['Thumb'] = QT
                    Q_list['Index'] = QI
                    Q_list['Middle'] = QM
                    Q_list['Ring'] = QR
                    Q_list['Little'] = QL
                    Q_list['Hand'] = QH
                    gesture = dict()
                    gesture['tag'] = idx
                    gesture['Quaternion'] = Q_list
                    if 'dataset' not in content:
                        content['dataset'] = dict()
                    content['dataset'][frame_count] = gesture
                    frame_count += 1
                    content['frame_count'] = frame_count
                    num += 1
                    print(f'get sample {num}')
                else:
                    flag = False
                if keyboard.is_pressed('q'):
                    break
        f.write(json.dumps(content, indent=4))


esp32port = 5


def main():
    ser = Serial(f'/dev/pts/{esp32port}')
    print('Opening ' + ser.name)
    while True:
        print('// Mode 0 for displaying current gesture data')
        print('// Mode 1 for collecting gesture data for building dataset')
        print('// Mode 2 for defining gestures used for l2 algorithm')
        ret = input('Select mode: ')
        if ret[-1] == 'q':
            break
        elif ret[-1] == '0':
            display(ser)
        elif ret[-1] == '1':
            collect(ser, 'Mode 1')
        elif ret[-1] == '2':
            collect(ser, 'Mode 2')
        else:
            print('Error: Mode Unsupported!')


if __name__ == '__main__':
    main()
