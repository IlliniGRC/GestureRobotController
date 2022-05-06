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

## 2022-03-10 - Bluetooth

## 2022-03-16 - L2 Algorithm Design

## 2022-03-18 - Euler Angles, Rotation Matrix, or Quaternion?

There three popular orientation representation systems: Euler angles, rotation matrix, and Quaternions. Euler angles are intuitive and Human-readable but suffer from singularities. Rotation matrix works fine in theory, but it needs 9 entries to store orientation, and needs more computing power compared with Quaternions which only have 4 elements for one orientation in 3D space. It is also easy to compute geodesic differences between two groups of Quaternions. So, Quaternions are used as our primary data structure to store IMU orientation information, but Euler angles are also used for debugging.

## 2022-03-21 - Bluetooth

## 2022-03-23 - First PCB Board Soldering and Verification

![first pcb board](/notebook/guang/first%20pcb.jpg)

## 2022-03-26 - Encryption & JSON

## 2022-03-28 - Redesign Power System & Second PCB Design

![power system 1.0](/notebook/guang/first%20power%20system.png)

The main target for the power supply module is to step up the 3.7 voltage from Lithium battery to 5 voltage and provide power for two ESP32 chips, sensors like IMUs, and actuators like LCD screen, LED, and vibration motor. The first version designed by Eric failed but he still hasn’t found the precise problem because the design is somewhat too complicated to analyze the correct behaviors for each component. The output port simply has no voltage, and we checked that soldering and wiring are correct, so it must be the design issue.

![power system 2.0](/notebook/guang/second%20power%20system.png)

## 2022-04-02 - AI Model Design

## 2022-04-05 - Choose L2 Algorithm Instead of AI

## 2022-04-07 - from Quaternions to Euler Angles and Rotation Matrix

![Quaternions to Euler angles](/notebook/guang/Q2Euler.svg)

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
