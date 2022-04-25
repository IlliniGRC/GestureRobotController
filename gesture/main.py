import argparse
import json
import time
import threading
import subprocess
import numpy as np
from serial import Serial
from l2_squared_error import l2_squared_error
from pyquaternion import Quaternion

retry_s = 2

def controller_ble_connect():
    while True:
        print("Trying to connect to controller")
        subprocess.run(["ble-serial", "-d", "30:83:98:7A:E4:06", "-p", "/tmp/ttyBLE10", 
            "-w", "6e400002-b5a3-f393-e0a9-e50e24dcca9e", 
            "-r", "6e400003-b5a3-f393-e0a9-e50e24dcca9e"], stdout=subprocess.DEVNULL)
        print(f"Controller connecting failed, try again after {retry_s} sec...")
        time.sleep(retry_s)

def robot_ble_connect():
    while True:
        print("Trying to connect to robot")
        subprocess.run(["ble-serial", "-d", "30:C6:F7:23:83:D2", "-p", "/tmp/ttyBLE11", 
            "-w", "6e400002-b5a3-f393-e0a9-e50e24dcca9e", 
            "-r", "6e400003-b5a3-f393-e0a9-e50e24dcca9e"], stdout=subprocess.DEVNULL)
        print(f"Robot connecting failed, try again after {retry_s} sec...")
        time.sleep(retry_s)

# Controller
# ble-serial -p /tmp/ttyBLE10 -d 30:83:98:7A:E4:06 -w 6e400002-b5a3-f393-e0a9-e50e24dcca9e -r 6e400003-b5a3-f393-e0a9-e50e24dcca9e

# Robot
# ble-serial -p /tmp/ttyBLE11 -d 30:C6:F7:23:83:D2 -w 6e400002-b5a3-f393-e0a9-e50e24dcca9e -r 6e400003-b5a3-f393-e0a9-e50e24dcca9e

controllerPort = "/tmp/ttyBLE10"
robotPort = "/tmp/ttyBLE11"


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
    controller_ble_thread = threading.Thread(target=controller_ble_connect)
    robot_ble_thread = threading.Thread(target=robot_ble_connect)
    controller_ble_thread.start()
    time.sleep(1)
    robot_ble_thread.start()

    input()
    controller = Serial(controllerPort)
    robot = Serial(robotPort)
    print('Opening controller: ' + controller.name)
    print('Opening robot: ' + robot.name)

    Q_list = dict()
    QT = list()
    QI = list()
    QM = list()
    QR = list()
    QL = list()
    QH = list()

    with open('gesture_l2.json', 'r') as f:
        l2_database = json.load(f)

    count = 0
    feedback_count = 0
    init_z = 0
    flag_init = True
    while True:
        count += 1
        controller.flush()
        robot.flush()
        report = controller.read_until(expected=b"\r\n")
        if len(report) % 15 != 2:
            continue
        index = 0
        while index < len(report) - 2:
            identifier, quaternions, accelerometers = report[index:index + 1], report[index + 1:index + 9], report[index + 9:index + 15]
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
        elif args.method == 'l2' and count % 3 == 0:
            gesture = l2_squared_error(Q_list, l2_database, 5)
            print(f'\nPrediction: {gesture}')
            if gesture == 404:
                if feedback_count >= 10:
                    feedback_count = 0
                    controller.write(b"b,0")
                else:
                    feedback_count += 1
            if gesture == 0:
                if feedback_count >= 10:
                    feedback_count = 0
                    controller.write(b"b,1")
                else:
                    feedback_count += 1
                angle = Q2Euler(Quaternion(QH))
                flag_init = False
                init_z = angle[2]
                print("hld|")
                robot.write(b'hld|')
            if not flag_init and gesture == 1:
                if feedback_count >= 10:
                    feedback_count = 0
                    controller.write(b"b,2\nm,1")
                else:
                    feedback_count += 1
                angle = Q2Euler(Quaternion(QH))
                z_move = angle[2] - init_z
                # print(angle / np.pi * 180)
                if abs(angle[1] * 100) < 20:
                    angle[1] = 0
                if abs(angle[0] * 150) < 25:
                    angle[0] = 0
                if abs(z_move * 100) < 25:
                    z_move = 0
                ch0, ch1, ch2 = int(-angle[1] * 100), int(angle[0] * 150), int(-z_move * 100)
                ch0_bytes = ch0.to_bytes(2, "big", signed=True)
                ch1_bytes = ch1.to_bytes(2, "big", signed=True)
                ch2_bytes = ch2.to_bytes(2, "big", signed=True)
                buffer = b'chs|' + ch0_bytes + ch1_bytes + ch2_bytes
                print(buffer)
                robot.write(buffer)
            if not flag_init and gesture == 2:
                if feedback_count >= 5:
                    feedback_count = 0
                    controller.write(b"m,3")
                else:
                    feedback_count += 1
                angle = Q2Euler(Quaternion(QH))
                z_move = angle[2] - init_z
                if abs(angle[0] * 150) < 20:
                    angle[0] = 0
                if abs(z_move * 100) < 22:
                    z_move = 0
                ch3, ch2 = int(angle[0] * 150), int(-z_move * 100)
                ch3_bytes = ch3.to_bytes(2, "big", signed=True)
                ch2_bytes = ch2.to_bytes(2, "big", signed=True)
                buffer = b'gim|' + ch3_bytes + ch2_bytes
                print(buffer)
                robot.write(buffer)
            if not flag_init and gesture == 3:
                print("sho|")
                robot.write(b"sho|")
            print(u'{}[2J{}[;H'.format(chr(27), chr(27)), end='')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ECE 445 Project')
    parser.add_argument('--method', type=str, default='l2', help='gesture recognition method, [l2]')
    args = parser.parse_args()
    main(args)
