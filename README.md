# **Gesture Robot Controller**

## **Project proposal**

### **Problem**

Traditionally, different robots are controlled by their specialized controller from different companies, and it takes time to learn how to smoothly and naturally use them. We propose a gesture control system that build upon the system, making the process of controlling a robot simple and fun.

![Visual Aid](https://github.com/0-EricZhou-0/GestureRobotController/blob/24163eae153ecba82c3c52a8171683d5026e511e/visual_aid.png)

### **Solution**

We plan to design a robot controller which can recognize human gestures and send corresponding commands to robots. The system will have three high-level requirements.

The first one is that the controller mounted on the user would be able to read the sensors placed on the body of the user and calculate the position of different body parts of the user and broadcast through Bluetooth.

The second one is that it would enable the gestures and movements of the user to be translated to actual robot controlling actions through a software running on a powerful device (like PC) after receiving data using Bluetooth, and it would also have the capability of commanding the robot using another Bluetooth link.

The third one is that it would be able to transmit the warnings of robots to signals that can be sensed by humans through actuators placed on the user, like lights (LEDs), vibration motors, and buzzers.

## **Design**

### **Block Diagram**

![Block Diagram](https://github.com/0-EricZhou-0/GestureRobotController/blob/main/block_diagram.png)

### **Subsystem Overview**

#### **Human Positioning System**

The system consists of a power source, a embedded processor, multiple IMUs, and a transceiver. Firstly, the IMUs are placed on user's body, and the user will input the locations of these sensors to the embedded processor. The embedded processor will constantly read data from the IMUs using I2C protocol, then it will calculate the position of these IMUs in the space. Together with user predefined IMU position, it will work out the positions and orientations of user's body parts. After that, the transceiver will output these raw data to PC through 2.45GHz Bluetooth data-link.

#### **Gesture Control System**

The system would be a software resides on the PC. It will take in the raw data transferred by transceiver of the Human Positioning System, and detect gestures using those data. Ideally, it can recognize many gestures such as motion of arm, motion of leg, making a fist, waving arms, shake head, etc. depending on the positions of the IMUs placed on the user. Then the system will generate controls based on these gestures, and send to the robot using another 2.45GHz Bluetooth data-link.

##### **Robot Feedback System**

The system would be a program resides on both PC and embedded processor of the controller. It will be used to transfer some signals generated by the robot back to the user through the actuators placed on user. It will also use the same 2.45GHz Bluetooth data-link that the controller used to communicate with PC, sending the signals to trigger vibration motors, LEDs, and buzzers on the controller.

### **Subsystem Requirements**

#### **Human Positioning System**

- It should be able to read the data from 9-axis IMUs through IIC protocol.
- It should be able to translate the readings into angles or other easy-to-understandable parameters
- It can transmit the results of calculation to PC or robot controller for them to interpret the data.

#### **Gesture Control System**

- It should be able to recognize at least the gestures of users listed below

  - Making a fist to stop the robot from moving
  - Extend the fingers, then the robot will move in direction where the user's palm is directed to.

- It would be able to translate these predefined gesture to robot movements.
- It can transmit the corresponding robot commands to the robot using Bluetooth datalink.

#### **Robot Feedback System**

- It should be able to receive signals sent from PC or controller on the robot.
- It should be able to interpret the feedback signals from the robot and control the following devices mounted on user

  - LED (array) blinking
  - Buzzer play predefined sound sequence
  - Vibration motor turning

### **Tolerance Analysis**

Gesture recognition algorithm is the most difficult part for us, since none of us has related experience on it. We currently only plan to recognize static gestures, but dynamic gestures clearly have more potential.

## **Ethics and Safety**

### User Safety

1. Since our product will directly contact human skin, it is important to separate skin from electricity and make sure that no hazardous components will put users in danger.

2. When power is low, the product should notify user and shutdown the system automatically to prevent battery from starvation. If the system is not in use in a long time, it should also shutdown by itself.

### Build Safety

1. Always power off the battery before any hardware changes. Rubber gloves are required before touching any electric components.
