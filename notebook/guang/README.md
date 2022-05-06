# Guang Worklog

## 2022-02-02 - Discussion for the Initial Idea

The initial idea is pretty simple: use gesture to control robot, and we all agree that it would be very cool. However, it is hard to figure out how to achieve this and break it down into pieces. In industry, the most popular solution is to use optical motion capture systems which use cameras to capture and locate markers on objects and then trace their motions. However, it is expensive and if the marker is blocked by something, the motion tracing would be lost. So we plan to make it easier and more accessible by using other sensors to capture user gestures.

## 2022-02-06 - Discussion for How to Capture Gestures

Today, we discussed how to measure the position and orientation of the fingers and arms of the user and then output these data to the PC.
The orientation of each finger can be divided into the flex of three joints, so resistance of flex sensors indicates the degree of flex for each finger, just like the power glove used by Nintendo Entertainment System. The other solution is to mount IMUs on each finger and measure the Euler angles of fingertips in 3D space.

|  | **Pros** | **Cons** |
|---|---|---|
| **Flex Sensor** | 1. Cheap ($10.95 each).<br/>2. Easy to use (only need to measure its resistance). | 1. Might not be accurate enough for our project, especially when two gestures are similar.<br/>2. Users can feel the resistive force from the flex sensor, which may downgrade the user experience. |
| **Inertial Measurement Unit** | 1. Extremely accurate and can directly output Euler angles for gesture recognition.<br/>2. Lightweight and will not interfere with user motions | 1. Expensive ($31.9 each)<br/>2. Need calibration after several times of measurements.<br/>3. Output depends on the magnetic field, which may change in different environments. |

Flex sensors are easy to use and achieve our target to some degree. However, since IMU can output measurement results that are much more accurate, which is essential for the Gesture Control System that will be explained later, IMU are chosen as our primary sensor.

## 2022-02-08 - Project Proposal

We finally decide to divide the whole project into three subsystems.

1. Human Positioning System
> It consists of 6 IMUs and ESP32. IMUs would collect the orientation data for each finger and palm and ESP32 would receive data and output the Euler angles to PC
2. Gesture Control System
> After receiving Euler angles for each IMUs, PC runs the gesture recognition algorithm to recognize gesture and send the corresponding command to robot.
3. Robot Feedback System
> If anything wrong, robot should send signals to user to indicate its current state through vibration, screen, buzzer, LEDs, and other actuators.

![subsystems](/notebook/guang/subsystems.png)

## 2022-02-15 - L2 Algorithm or AI

The most difficult and major task is to design an algorithm to recognize and differentiate gestures. There are two methods that come to mind: L2 algorithm and AI model. The key idea behind the L2 algorithm is simple: compare the current gesture with each gesture in the database, calculate the L2 error between each pair, and output the gesture with the lowest L2 error. The AI model is also suitable and it may work even better than the L2 algorithm. For example, the L2 algorithm may find it hard to recognize two similar gestures, but AI may find the key feature to distinguish them. Also, since the gesture will continue to be the same one in a short time, the Markov chain can be extremely useful to increase accuracy in AI models.

The comparison table:

|  | **Pros** | **Cons** |
|---|---|---|
| **L2** | 1. Easy to implement<br/>2. Can manually adjust the sensitivity, so in some cases, it will output "no gesture"<br/>3. New gesture can be added into database easily | 1. It assumes that user gestures are static, and only uses information about orientation angles |
| **AI** | 1. Can utilize dynamics like acceleration to recognize gesture<br/>2. By using Markov chain, the previous prediction can also help the next prediction<br/>3. Universal and general. In theory, it should perform better than L2 algorithm | 1. Hard to train and deploy<br/>2. Performance greatly influenced by the quality of dataset<br/>3. The prediction labels are fixed, so it would be difficult to add a new gesture<br/>4. Collecting dataset may consume us too much time |

I will try both methods, and compare their performance in different settings. But, if we do not have enough time in the final stage, I may abandon the AI model method.

## 2022-02-19 - Find Suitable Modules for Our Project

Considering the fact that gesture recognition may need the measurement to be extremely precise, the requirement for IMU is quite high. After searching online, WT901 is the best IMU that we can find and afford.

![WT901](/notebook/guang/WT901.jpg)

> Item: [WitMotion WT901](https://www.wit-motion.com/gyroscope-module/Witmotion-wt901-ttl-i2c.html)
> 
> Buy: [Amazon](https://www.amazon.com/Accelerometer-Acceleration-Gyroscope-Electronic-Magnetometer/dp/B07GBRTB5K/)

Its resolution is 0.005g for acceleration, 0.61°/s for gyroscope, 16 bits for magnetic field, which is extremely high. It also has three irresistible features:

1. It supports I2C protocol, so we only need 4 wires to connect all IMUs and the STM32 (including powering IMUs). This makes the wiring and design much simpler.
2. The producer provides free and genuinely useful software, so we can easily calibrate IMUs with a single UART serial port. It is also useful for debugging for our project.
3. The normal IMU only outputs the raw data from accelerometer, gyroscope, and magnetometer, and these signals always have noises. But WT901 can directly output Euler angles and quaternions after Kalman filtering which makes it reliable and stable in most environment.

> Item: STM32F427 / 407
> 
> Buy: [AliExpress 427](https://www.aliexpress.com/premium/stm32f427.html) / [407](https://www.aliexpress.com/premium/stm32f407.html)

### Future Problems

1. Soldering chip is complicated and chips are fragile. We need professional engineers to help us.

2. Need funding to buy stuffs.

## 2022-02-25 - ESP32 Instead of STM32

We originally planned to use STM32 as our micro controller unit. However while designing our first PCB board, we found out that STM32 needs too many peripheral components to operate and it is not easy to program and write code for STM32 even though it is extremely powerful. The most inconvenient thing is that we are not allowed to use external bluetooth modules, and designing a bluetooth module by ourselves is too complicated and out of our ability. Then we find that EPS32 may be our better solution.

The comparison table:

|  | **Pros** | **Cons** |
|---|---|---|
| **STM32** | 1. Extremely powerful<br/>2. Professional<br/>3. Nearly all communication protocols are supported | 1. Expensive<br/>2. Need external modules to enable Bluetooth<br/>3. Difficult to write code and program it<br/>4. It has too many pins which makes hand soldering nearly impossible |
| **ESP32** | 1. Builtin Bluetooth and WIFI module<br/>2. Cheap<br/>3. Support MicroPython library, so it is much easier to write code and debug<br/>4. It has small number of pins, but they are all universal | 1. Compute capability may not be enough (need verification) |

So, after comparison and discussion, we decide to use ESP32 instead of STM32.

## 2022-02-29 - PCB Review

We are told that our PCB is not sophisticated enough as senior project, and we should leave debugging pins to make sure that when one or two modules malfunction, other modules and microcontroller can still work. So we plan to use two ESP32 to perform different tasks and connect them through a UART port. To increase complexity, two OLED screens are added, so do buzzer, vibration motor, and two LEDs.

The schematic for two ESP32:
![MCU](/notebook/guang/MCU.png)

## 2022-03-05 - IMU & I2C

WT901 IMU supports two common communication protocols: UART and I2C.
UART is bidirectional but one wire can only connect two devices, so if we use UART to connect 6 IMUs with ESP32, we need 6 UART. However, I2C can connect any number of devices into one wire but the data bandwidth is much less than UART. So, we use UART for calibration on PC and I2C to transfer data between IMUs and ESP32.

The UART connection view:

![IMU_UART](/notebook/guang/IMU_UART.png)

To connect IMUs and ESP32 in one I2C line, we only need to connect them in parallel.

The I2C connection view:

![IMU_I2C](/notebook/guang/IMU_I2C.png)

Note here that the two 4.7K resistors are necessary to make the connection stable. The value of resistance may depends on how many devices are connected in I2C, but here two 4.7K resistors are enough for our project.

For calibration, we need to calibrate accelerometer and magnetometer separately. To calibrate accelerometer, we only need to hold the IMU static and press the button on calibration software. However, magnetometer calibration is much more complicated. There are 6 different calibration methods in total, so I tried all of them and found that ellipsoid fitting method works best for us. Other methods always have some degree of offset from real value after calibration, but ellipsoid fitting method does not have such problem.

To differentiate different IMUs, they need different I2C addresses, so ESP32 can know which IMU corresponds to which finger. The configuration that we use for our project is listed in the table below.

|  | **I2C Address** |
|---|---|
| **Middle** | 0x207 |
| **Ring** | 0x206 |
| **Little** | 0x205 |
| **Thumb** | 0x209 |
| **Hand** | 0x20A |
| **Index** | 0x208 |

## 2022-03-10 - Bluetooth

I mainly develop ESP32 with MicroPython library and it supports some low-level BLE APIs.
My first simple version failed to connect with PC, but somehow it can pair and communicate with my iPad. It turns out that there are four BLE GAP roles: Broadcaster, Observer, Peripheral, and Central. Previously, I used the default Broadcaster and Observer mode with unidirectional, connection-less communications which is not supported by most PCs, so it did not work. So, I have dived into the BLE protocol details and refactored the whole code to place ESP32 as Peripheral and PC as Central.

```python
_UART_UUID = bluetooth.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
_UART_TX = (
    bluetooth.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E'),
    _FLAG_READ | _FLAG_NOTIFY,
)
_UART_RX = (
    bluetooth.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E'),
    _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE,
)
```

I registered two services for ESP32. The first UUID indicates that the data is about the Heart Rate (clearly it is not true, but since it does not influence any function, I leave it unchanged) and the next UUID marks the channels as Tx and Rx for transmitting and receiving message.
My first implementation is quite naïve, but it demonstrates the general procedure to make the BLE works.

![BLE 1.0](/notebook/guang/ble_1.0.jpg)

## 2022-03-16 - Euler Angles, Rotation Matrix, or Quaternion?

There three popular orientation representation systems: Euler angles, rotation matrix, and Quaternions. Euler angles are intuitive and Human-readable but suffer from singularities. Rotation matrix works fine in theory, but it needs 9 entries to store orientation, and needs more computing power compared with Quaternions which only have 4 elements for one orientation in 3D space. It is also easy to compute geodesic differences between two groups of Quaternions. So, Quaternions are used as our primary data structure to store IMU orientation information, but Euler angles are also used for debugging.

## 2022-03-18 - L2 Algorithm Design

L2 algorithm only uses Euler angles to distinguish different gestures, and it assumes that the gesture is static (do not consider acceleration and location in space). It only considers the relative angles between fingers and wrist.

![l2 math](/notebook/guang/l2%20equation.png)

The main idea is to use the L2 loss function to calculate the errors between the current orientations of user fingers and these in database and choose the gesture with the lowest error, as demonstrated by the equation.

The implementation code is here.

```python
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
```

Note that I add sensitivity parameter to control the range of gestures that should be recognized as “No Gesture” when the error of the best match is too large.

## 2022-03-21 - Bluetooth

Continue to refine the code for Bluetooth function on ESP32.

The first version that I implemented last time can not handle the situation when the connection loses after previous connection and to make sure that all messages will be handled and no computing power is wasted, the method for receiving message should be interrupt instead of polling. So, Interrupt Request (IRQ) is used to handle all functions in the second implementation.

![BLE 2.0](/notebook/guang/ble_2.0.jpg)

The IRQ handling code of the second implementation is here.

```python
class BLESimplePeripheral:
    def __init__(self, ble, name='BLE'):
        self.led = Pin(2, Pin.OUT)
        self.timer1 = Timer(0)
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle_tx, self._handle_rx),) = self._ble.gatts_register_services((_UART_SERVICE,))
        self._connections = set()
        self._write_callback = None
        self._payload = advertising_payload(name=name, services=[_UART_UUID])
        self.timer1.init(period=100, mode=Timer.PERIODIC, callback=lambda t: self.led.value(not self.led.value()))
        self._advertise()
 
    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            self.led.on()
            self.timer1.deinit()
            conn_handle, _, _ = data
            print('New connection', conn_handle)
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            self.timer1.init(period=100, mode=Timer.PERIODIC, callback=lambda t: self.led.value(not self.led.value()))
            conn_handle, _, _ = data
            print('Disconnected', conn_handle)
            self._connections.remove(conn_handle)
            # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            value = self._ble.gatts_read(value_handle)
            if value_handle == self._handle_rx and self._write_callback:
                self._write_callback(value)
```

On the Linux PC side, I find a library called ble-serial to map the Bluetooth input and output channels into a virtual serial port, so I can access and process the data flow normally.

```bash
ble-scan -d 78:E3:6D:18:14:EE
```

This command is used to scan whether the ESP32 with the specified MAC address exists.

```bash
ble-serial -p /tmp/ttyBLE0 -d 78:E3:6D:18:14:EE -w 6e400002-b5a3-f393-e0a9-e50e24dcca9e -r 6e400003-b5a3-f393-e0a9-e50e24dcca9e
```

Connect to the ESP32 and map it into a virtual serial port /tmp/ttyBLE0.

```bash
screen /tmp/ttyBLE0
```

Open the virtual serial port in terminal, so I can read and write through keyboard to ESP32 by BLE.

## 2022-03-23 - First PCB Board Soldering and Verification

![first pcb board](/notebook/guang/first%20pcb.jpg)

## 2022-03-26 - Encryption & JSON

## 2022-03-28 - Redesign Power System & Second PCB Design

The main target for the power supply module is to step up the 3.7 voltage from Lithium battery to 5 voltage and provide power for two ESP32 chips, sensors like IMUs, and actuators like LCD screen, LED, and vibration motor. The first version designed by Eric failed but he still hasn’t found the precise problem because the design is somewhat too complicated to analyze the correct behaviors for each component. The output port simply has no voltage, and we checked that soldering and wiring are correct, so it must be the design issue.

![power system 1.0](/notebook/guang/first%20power%20system.png)

So, I decide to redesign the whole module from scratch and find a chip that can fulfill the requirement easily. Through searching on Google, I find that ME2108 is the most popular IC solution and matches my need.

![power system 2.0](/notebook/guang/second%20power%20system.png)

There are four peripheral components: switch, inductor, diode, and two capacitors. The function of switch is simple. It is purely used to turn on and off the wearable device. When turning off the device, to prevent the input from floating, one side of the switch should connect with the ground instead of nothing. Inductor is used to filter out the high frequency noise that may enter the Lx input. Capacitors are used to smooth the output voltage. Diode is used to prevent reverse current that may damage the ME2108 IC chip.

![power system pcb](/notebook/guang/power_system_second_pcb.png)

From the tips of ME2108 datasheet[^1], I set these external components as close as possible to the IC and minimize the connection between the components and the IC while wiring to prevent the parasitic capacitance and inductance effect. Also, because zero level within IC may vary with the switching current which causes unstable operation of ME2108 chip, I make Vss pin sufficient grounding.

## 2022-04-02 - AI Model Design

I use PyTorch library to implement and train my AI model. Here are two designs. The simple one with only two layers and complex one with five layers to see if adding more layers would help to recognize gesture and raise the correctness rate.

The neural network with two layers:

```python
super(NeuralNet, self).__init__()
hidden_units = 32
self.model = nn.Sequential(
    nn.Linear(in_size, hidden_units),
    nn.ReLU(),
    nn.Linear(hidden_units, out_size),
)
self.loss_fn = loss_fn
self.optimizer = optim.SGD(self.model.parameters(), lr=lrate)
```

The neural network with five layers:
```python
super(NeuralNet, self).__init__()
hidden_units_1 = 96
hidden_units_2 = 48
hidden_units_3 = 24
hidden_units_4 = 12
self.model = nn.Sequential(
    nn.Linear(in_size, hidden_units_1),
    nn.ReLU(),
    nn.Linear(hidden_units_1, hidden_units_2),
    nn.ReLU(),
    nn.Linear(hidden_units_2, hidden_units_3),
    nn.ReLU(),
    nn.Linear(hidden_units_3, hidden_units_4),
    nn.ReLU(),
    nn.Linear(hidden_units_4, out_size),
)
self.loss_fn = loss_fn
self.optimizer = optim.SGD(self.model.parameters(), lr=lrate)
```

The input is Euler angles, quaternion, accelerometer, gyroscope, and magnetometer. It is a 96 floats array. The output is the best math gesture index in database encoded in one-hot arrays. I just finished writing code for these modes. The training and adjusting parameters like learning rate, number of layers, and number of hidden units will start in the next week.

## 2022-04-05 - Choose L2 Algorithm Instead of AI

## 2022-04-07 - from Quaternions to Euler Angles and Rotation Matrix

By searching online, I find equations[^2] to convert Quaternions to Euler angles.

![Quaternions to Euler angles](/notebook/guang/Q2Euler.svg)

My code implementation is here:

```python
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
```

Since rotation matrix is also one of the most common method to representation orientation in 3D space, I also find the equations[^3] to convert Quaternions to rotation matrix.

![Quaternions to rotation matrix](/notebook/guang/Q2matrix.svg)

My code for it:

```python
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
```

## 2022-04-12 - Prepare Robot for Demo

## 2022-04-17 - Integrate Everything Together

## 2022-04-23 - 3D Printing Box

In order to protect users skim from any possible electrical damage and make our project more engaging, I decide to design and print a box to contain our PCB board.

The requirements are listed below:

1. Screens, LEDs, I2C ports, buttons, switch, battery charge port, and Micro-USB port should be exposed to user, but other electric components should not.
2. Should includes a small area to contain the battery inside.
3. Should have two mounting points, so the device can be mounted on arms.z

Besides, I also plan to design 6 containers for IMUs.

The design view in Autodesk Fusion 360:

![box](/notebook/guang/box.png)

The 3D printing slicing view in Cura:

![3d printing](/notebook/guang/3d%20print.png)

The final physical appearance:

![final](/notebook/guang/final.jpeg)

## 2022-04-24 - Prepare Robot for Demo

[^1]: Micro One, “ME2108 Datasheet,” Nanjing Micro One Electronics Inc. \[Online\]. Available: http://www.microne.com.cn/EN/downloads.aspx?cid=17&id=51. \[Accessed: 30-Mar-2022\].

[^2]: “Conversion between quaternions and Euler angles,” Wikipedia, 28-Mar-2021. \[Online\]. Available: https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles.\[Accessed: 07-Apr-2022\]. 

[^3]: “Quaternions and spatial rotation,” Wikipedia, 02-Aug-2020. \[Online\]. Available: https://en.wikipedia.org/wiki/Quaternions_and_spatial_rotation. \[Accessed: 07-Apr-2022\]. 
