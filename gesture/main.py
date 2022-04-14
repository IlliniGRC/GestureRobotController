# from l2_squared_error import *
#
# if __name__ == '__main__':
#     data = np.array([[1, -1, 1], [1.4, -1, 1], [1, -1, 1], [1, -1, 1], [1, -1, 1], [1, -1, 1]])
#     print(l2_squared_error(data, 0.5))

import argparse


def main(args):
    if args.method == 'neural':
        print('use neural')
    elif args.method == 'l2':
        print('use l2')
    else:
        print('Method Error!')
        return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ECE 445 Project')
    parser.add_argument('--method', type=str, default='neural', help='gesture recognition method, [neural]')
    args = parser.parse_args()
    main(args)
