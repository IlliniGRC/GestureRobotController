import threading
import numpy as np
import subprocess
import time
from l2_squared_error import l2_squared_error_to_file
from pyquaternion import Quaternion
from serial import Serial
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

def keyboard_thread():
    input()
    return


def collect(port, mode):
    if mode == 'Mode 1':
        file_name = 'dataset.json'
    elif mode == 'Mode 2':
        file_name = 'gesture_l2.json'
    else:
        print('Mode Error!')
        return
    content = {}
    with open(file_name, 'w') as f:
        while True:
            idx = input(f'Gesture idx: ')
            if idx == '' or idx[-1] == 'q':
                break
            if not idx.isnumeric():
                print(f"Invalid input <{idx}>")
                continue
            idx = int(idx)
            press_thread = threading.Thread(target=keyboard_thread)
            press_thread.start()
            print(f"Press <Enter> to Sample Gesture Index <{idx}>")
            while True:
                report = port.read_until(expected=b"\r\n")
                if len(report) % 15 != 2:
                    continue
                if not press_thread.is_alive():
                    Q_list = {}
                    index = 0
                    while index < len(report) - 2:
                        identifier, quaternions = report[index:index + 1], report[index + 1:index + 9]
                        index += 15
                        q0 = np.short(quaternions[1] << 8 | quaternions[0]) / 32768
                        q1 = np.short(quaternions[3] << 8 | quaternions[2]) / 32768
                        q2 = np.short(quaternions[5] << 8 | quaternions[4]) / 32768
                        q3 = np.short(quaternions[7] << 8 | quaternions[6]) / 32768
                        Q = list(np.array([q0, q1, q2, q3]))
                        if identifier not in [b"T", b"I", b"M", b"R", b"L", b"H", b"A"]:
                            print(f" Invalid Identifier <{identifier}>")
                            continue
                        Q_list[identifier.decode()] = Q
                    content[idx] = Q_list
                    print(f'Get Sample For Gesture {idx}')
                    break
        f.write(json.dumps(content, indent=2))

def to_file(port: Serial):
    content = {}
    with open('gesture_l2.json', 'r') as f:
        l2_database = json.load(f)

    with open("database.bin", 'w') as f:
        port.flush()
        while True:
            press_thread = threading.Thread(target=keyboard_thread)
            press_thread.start()
            print(f"Press <Enter> to exit sampling")
            while True:
                report = port.read_until(expected=b"\r\n")
                if len(report) % 15 != 2:
                    continue
                if not press_thread.is_alive():
                    print("Gathering process killed")
                    return
                Q_list = {}
                index = 0
                while index < len(report) - 2:
                    identifier, quaternions = report[index:index + 1], report[index + 1:index + 9]
                    index += 15
                    q0 = np.short(quaternions[1] << 8 | quaternions[0]) / 32768
                    q1 = np.short(quaternions[3] << 8 | quaternions[2]) / 32768
                    q2 = np.short(quaternions[5] << 8 | quaternions[4]) / 32768
                    q3 = np.short(quaternions[7] << 8 | quaternions[6]) / 32768
                    Q = list(np.array([q0, q1, q2, q3]))
                    if identifier not in [b"T", b"I", b"M", b"R", b"L", b"H", b"A"]:
                        print(f" Invalid Identifier <{identifier}>")
                        continue
                    Q_list[identifier.decode()] = Q
                to_append = l2_squared_error_to_file(Q_list, l2_database, 4)
                print(to_append)
                f.write(to_append)
                print(u'{}[2J{}[;H'.format(chr(27), chr(27)), end='')

retry_s = 2
controllerPort = "/tmp/ttyBLE10"

def controller_ble_connect():
    while True:
        print("Trying to connect to controller")
        subprocess.run(["ble-serial", "-d", "30:83:98:7A:E4:06", "-p", "/tmp/ttyBLE10", 
            "-w", "6e400002-b5a3-f393-e0a9-e50e24dcca9e", 
            "-r", "6e400003-b5a3-f393-e0a9-e50e24dcca9e"], stdout=subprocess.DEVNULL)
        print(f"Controller connecting failed, try again after {retry_s} sec...")
        time.sleep(retry_s)

def main():
    controller_thread = threading.Thread(target=controller_ble_connect)
    controller_thread.start()

    input()
    ser = Serial(controllerPort)
    while True:
        print('// Mode 0 for displaying current gesture data')
        print('// Mode 1 for collecting gesture data for building dataset')
        print('// Mode 2 for defining gestures used for l2 algorithm')
        print('// Mode 3 for collecting gesture data to file')
        ret = input('Select mode: ')
        if ret[-1] == 'q':
            exit(1)
        elif ret[-1] == '0':
            display(ser)
        elif ret[-1] == '1':
            collect(ser, 'Mode 1')
        elif ret[-1] == '2':
            collect(ser, 'Mode 2')
        elif ret[-1] == '3':
            to_file(ser)
        else:
            print('Error: Mode Unsupported!')


if __name__ == '__main__':
    main()
