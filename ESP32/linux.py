import serial
import json


def decrypt(text, key=0):
    if not isinstance(text, str):
        raise TypeError('{} should be a type string'.format(text))
    if not isinstance(key, int):
        raise TypeError('{} should be of type int'.format(key))
    return ''.join([chr((ord(something) - key) % 128) for something in text])


user = serial.Serial('/dev/pts/2')
print('Opening ' + user.name)
while True:
    data_raw = decrypt(user.readline().decode('ascii').strip('\r\n'), 7)
    data = json.loads(data_raw)
    print(data)
