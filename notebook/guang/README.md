# Guang Worklog

## 2022-02-08 - Discussion for the Initial Idea

The initial idea is pretty simple: use gesture to control robot, and we all agree that it would be very cool. However, it is hard to figure out how to achieve this and break it down into pieces. In industry, the most popular solution is to use optical motion capture systems which use cameras to capture and locate markers on objects and then trace their motions. However, it is expensive and if the marker is blocked by something, the motion tracing would be lost. So we plan to make it easier and more accessible by using other sensors to capture user gestures.

## 2022-02-09 - Discussion for how to capture gestures

After discussion, we plan to use IMUs to measure the Euler angles of each finger. Since our target is not that fully reconstruct the position of each finger in 3D space but only recognize the gesture, so 5 IMUs for 5 fingers and one for palm are enough.

## 2022-02-11 - Find suitable modules for our project

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
