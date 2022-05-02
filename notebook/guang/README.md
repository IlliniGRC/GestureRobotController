# Guang Worklog

## 2022-02-02 - Discussion for the Initial Idea

The initial idea is pretty simple: use gesture to control robot, and we all agree that it would be very cool. However, it is hard to figure out how to achieve this and break it down into pieces. In industry, the most popular solution is to use optical motion capture systems which use cameras to capture and locate markers on objects and then trace their motions. However, it is expensive and if the marker is blocked by something, the motion tracing would be lost. So we plan to make it easier and more accessible by using other sensors to capture user gestures.

## 2022-02-06 - Discussion for how to capture gestures

After discussion, we plan to use IMUs to measure the Euler angles of each finger. Since our target is not that fully reconstruct the position of each finger in 3D space but only recognize the gesture, so 5 IMUs for 5 fingers and one for palm are enough.

## 2022-02-08 - Project proposal

We finally decide to divide the whole project into three subsystems.

1. Human Positioning System
> It consists of 6 IMUs and ESP32. IMUs would collect the orientation data for each finger and palm and ESP32 would receive data and output the Euler angles to PC
2. Gesture Control System
> After receiving Euler angles for each IMUs, PC runs the gesture recognition algorithm to recognize gesture and send the corresponding command to robot.
3. Robot Feedback System
> If anything wrong, robot should send signals to user to indicate its current state through vibration, screen, buzzer, LEDs, and other actuators.

![subsystems](/notebook/guang/subsystems.png)

## 2022-02-15 - L2 algorithm or AI

The most difficult and major task is to design an algorithm to recognize and differentiate gestures. There are two methods that come up into my mind: L2 algorithm and AI model. The key idea behind L2 algorithm is simple: compare the current gesture with each gesture in database, calculate the L2 error between each pair, and output the gesture with the lowest L2 error. AI model is also suitable and it may work even better than L2 algorithm. For example, L2 algorithm may find it hard to recognize two similar gestures, but AI may find the key feature to distinguish them. Also, since gesture will continue to be the same one in a short time, Markov chain can be extremely useful to increase accuracy in AI model.

The comparison table:

|  | **Pros** | **Cons** |
|---|---|---|
| **L2** | 1. Easy to implement<br/>2. Can manually adjust the sensitivity, so in some cases, it will output "no gesture"<br/>3. New gesture can be added easily | 1. Only uses information about angles |
| **AI** | 1. Can utilize dynamics like acceleration to recognize gesture<br/>2. By using Markov chain, the previous prediction can also help the next prediction<br/>3. Universal and general. In theory, it should perform better than L2 algorithm | 1. Hard to train and deploy<br/>2. Performance greatly influenced by the quality of dataset<br/>3. The prediction labels are fixed, so it would be difficult to add a new gesture<br/>4. Collecting dataset may consume us too much time |

I will try both methods, and compare their performance in different settings. But, if we do not have enough time in the final stage, I may abandon the AI model method.

## 2022-02-19 - Find suitable modules for our project

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

## 2022-02-23 - Design document

## 2022-02-25 - First PCB design

Requirements

## 2022-02-27 - ESP32 instead of STM32

We originally plan to STM32 as our micro controller unit. However whiling designing our first PCB board, we find out that STM32 needs to many peripheral components to operate and it is not easy to program and write code for STM32 even though it is extremely powerful. The most inconvenient thing is that we are not allowed to use external bluetooth modules, and designing a bluetooth module by ourselves is too complicated and out of our ability.
Then we find that EPS32 maybe our better solution.

The comparison table:

|  | **Pros** | **Cons** |
|---|---|---|
| **STM32** | 1. Extremely powerful<br/>2. Professional | 1. Expensive<br/>2. Need external modules to enable Bluetooth<br/>3. Difficult to write code and program it<br/>4. It has too many pins which makes hand soldering nearly impossible |
| **ESP32** | 1. Builtin Bluetooth and WIFI module<br/>2. Cheap<br/>3. Support MicroPython library, so it is much easier to write code and debug<br/>4. It has small number of pins, but they are all universal | 1. Compute capability may not be enough (need verification) |

So, after comparison and discussion, we decide to use ESP32 instead of STM32.

## 2022-02-29 - PCB review

## 2022-03-05 - IMU & I2C

## 2022-03-10 - Bluetooth

## 2022-03-16 - Design L2 algorithm

## 2022-03-18 - Quaternion is better than Euler angles

## 2022-03-21 - Bluetooth

## 2022-03-23 - First PCB board soldering and verification

## 2022-03-26 - Encryption & JSON

## 2022-03-28 - Redesign power system & Second PCB design

## 2022-04-02 - AI Model Design

## 2022-04-05 - Choose L2 Algorithm instead of AI

## 2022-04-07 - from Quaternions to Euler angles and rotation matrix

## 2022-04-12 - Prepare robot for demo

## 2022-04-17 - Integrate everything together

## 2022-04-23 - 3D printing box

In order to protect user skim from any possible electrical damage and make our project more engaging, I decide to design and print a box to contain our PCB board.

The requirements are listed below:

1. Screens, LEDs, I2C ports, buttons, switch, battery charge port, and Micro-USB port should be exposed to user, but other electric components should not.
2. Should includes a small area to contain the battery inside.
3. Should have two mounting points, so the device can be mounted on arms.

Besides, I also plan to design 6 containers for IMUs.

The design view in Autodesk Fusion 360:

![box](/notebook/guang/box.png)

The 3D printing slicing view in Cura:

![3d printing](/notebook/guang/3d%20print.png)

The final physical looking:

![final](/notebook/guang/final.jpeg)

## 2022-04-24 - Prepare robot for demo
