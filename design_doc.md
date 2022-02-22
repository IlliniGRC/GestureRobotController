# Design Document

## 1. Introduction

### Problem and Solution Overview

Traditionally, different robots are controlled by their specialized controller from different companies, and it takes time to learn how to smoothly and naturally use them. We propose a gesture control system that builds upon the system, making the process of controlling a robot simple and fun. We plan to design a robot controller which can recognize human gestures and send corresponding commands to robots. The system will have three high-level requirements.

### Visual Aid

![Visual Aid](visual_aid.png)

### High-level requirements list

The first one is that the controller mounted on the user would be able to read data from inertial measurement unit (IMU)s placed on fingers and wrists, calculate the relative positions and Euler angles (with L2 errors less than 3% in 1 minute) of different body parts of the user in the reference of wrists, and then broadcast through Bluetooth. The total delay for this part should be less than 20ms.

The second one is that it would recognize the current gesture in database with error rate less than 5% within 30ms on a powerful device like PC from data collected from controller (which can be done through algorithm or trained neural network), and then send the corresponding robot command to the controlled robot through Bluetooth. The total delay for this part should be less than 30ms.

The third one is that it would be able to receive the feedback information from robot through Bluetooth and display it to actuators on the gloves like lights (LEDs), vibration motors, and buzzers, so users can directly feel the current state of robot and decide the next command gesture based on that. The total delay for this part should be less than 20ms.

## 2. Design

### Block Diagram

![Block Diagram](block_diagram.png)

### Physical Design

### [SUBSYSTEM NAME]

### [SUBSYSTEM NAME]

### [SUBSYSTEM NAME]

### Tolerance Analysis

The IMUs will be measuring the magnetic field strength to calculate the angle of the unit. However, if the IMU is placed near a powerful external magnetic field source other than the earth (e.g. motors, large block of conductive metal, wall power cable/outlet), then the reading might be affected and produce garbage result. We will be examining the reasonable tolerance of data error and the real motion range of human finger.

## 3. Cost and Schedule

### Cost Analysis

Labor Costs:
According to the average annual salary of an electrical engineer, the hourly salary for each team member is $36/hour. And we expect to work 8 hours per week on this project.
The total labor cost would be: $36/hr × 2.5 × 8 weeks × 8hrs/week = $5, 760 per partner
The total cost of out team would be $17, 280.

Component Costs:

### Schedule

## 4. Discussion of Ethics and Safety

### Ethical and Safety Issues

User Safety

1. Since our product will directly contact human skin, it is important to separate the skin from electricity and make sure that no hazardous components will put users in danger. The wearable component in our design does not pose a threat to the user, and we will keep it operating under a low-voltage that reduces energy consumption.

2. When power is low, the product should notify the user and shut down the system automatically to prevent the battery from starvation. If the system is not in use for a long time, it should also shut down by itself. Our product utilizes Bluetooth protocol for wireless communication between the controller and the robot. We commit to protect and respect user privacy, complying with section 7.8.I-1 of IEEE’s guidelines.

Build Safety

1. Always power off the battery before any hardware changes. Rubber gloves are required before touching any electric components. We will treat all persons fairly and with respect, and to not engage in discrimination based on characteristics such as race, religion, gender, disability, age, national origin, sexual orientation, gender identity, or gender expression. We will also not engage in harassment of any form, including sexual harassment or bullying behavior.

### Procedures to Mitigate Concerns

## 5. Citations

[1] “IEEE code of Ethics,” IEEE. [Online]. Available: <https://www.ieee.org/about/corporate/governance/p7-8.html>. [Accessed: 21-Feb-2022].

[2] M. Zhu, Z. Sun, Z. Zhang, Q. Shi, T. He, H. Liu, T. Chen, and C. Lee, “Haptic-feedback smart glove as a creative human-machine interface (HMI) for virtual/augmented reality applications,” Science Advances, vol. 6, no. 19, 2020.
