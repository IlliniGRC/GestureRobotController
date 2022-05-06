# Haoduo's Worklog
2022-01-31 	Project Approval

2022-02-07 	Project Proposal

2022-02-14 	Design Document & Review

2022-02-28 	PCB Design

2022-03-14 	Circuit Build

2022-03-28 	Finalize the PCB

2022-04-04	Data Retrieval

2022-04-14	Testing & Demo

# 2022-01-31 	Project Approval
In our team's first meeting, we discussed the initial post made by Eric. His initial idea was to design a gesture controller compatible with all robots. TA suggested us to narrow our topic by choosing a specific robot. We decided to use the robot from Illini RoboMaster, which they were most familiar with. We made another post and successfully gained TA's approval.

# 2022-02-07 	Project Proposal
I created our initial block diagram. It was simple, contained the subsystems we needed. Our main focus was gesture data gathering and recognition. 

![Alt text](https://github.com/IlliniGRC/GestureRobotController/blob/main/notebook/haoduo/block_diagram.png)

# 2022-02-14 	Design Document & Review
We continued to work on the design document and attended the design review. TA offered a lot of suggestions. I studied a project from the previous semester about a glove that controlled drones. They used it to simulate the function of a mouse. We explained our logic to the head TA and asked him about the use of PCB. Our thought was to use a development board called Arduino ATmega328P, but this would not satisfy senior design's requirements. So we decided to build our own board.

# 2022-02-28 	PCB Design
I drew the first draft of our PCB board, including a basic processor, a Bluetooth module, and a power module. We then revised it and submitted the first-round PCB order. Meanwhile, we made a list of all the components we need, and I started to purchesing them. Hopefully they will arrive before the spring break.

![Alt text](https://github.com/IlliniGRC/GestureRobotController/blob/main/notebook/haoduo/pcb.png)

# 2022-03-14 	Circuit Build
With everything we needed, we started to solder the PCB board. Then Eric will test the Bluetooth function, and Guang and I will work on the gesture recognition algorithm. Guang proposed several approaches. I started with WT901's datasheet. WT901 is the IMU we use to collect each finger's position and orientation. Its manufacturer, WitMotion, developed a driver. Though we are not planning to use it, I looked at its configuration to find out what data we might need. For gesture recognition, we need Quaternion, Angle, and Angular Velocity. For calibration, we need Magnetic Field.

![Alt text](https://github.com/IlliniGRC/GestureRobotController/blob/main/notebook/haoduo/WT901_Driver.png)

# 2022-03-28 	Finalize the PCB
After testing the first-round PCB, we made some changes. We decided to add a buzzer and a display for feedback. Also, since one ESP32 is not powerful enough to handle all the tasks, we add another one. Based on our new needs, we redrew the PCB schematic. This is our new feedback system.

![Alt text](https://github.com/IlliniGRC/GestureRobotController/blob/main/notebook/haoduo/feedback.png)

# 2022-04-04	Data Retrieval
Before putting IMUs on the glove, I simulated some gestures to gather the data. With the input data, our program can save it as a gesture. These saved gestures are later used when compared to the gesture user is making. Then, we applied the L2 algorithm to determine the right gesture.

![Alt text](https://github.com/IlliniGRC/GestureRobotController/blob/main/notebook/haoduo/code.png)

![Alt text](https://github.com/IlliniGRC/GestureRobotController/blob/main/notebook/haoduo/dataset.png)

![Alt text](https://github.com/IlliniGRC/GestureRobotController/blob/main/notebook/haoduo/L2.png)

# 2022-04-14	Testing & Demo
After assembling all parts, we tested our product on the actual robot. We now have two major problems. Frist is the magnetic interference on Z-axis. If it is not calibrated, it will bring about a large measurement error and affect the accuracy of the Z-axis angle measurement of the heading angle. Second is the Bluetooth communication between the computer and the robot. The latency is below 100ms, which is acceptable. However, there are chances of losing connection. After fixing these two issues, I will move on to record the extra credit video.
![Alt text](https://github.com/IlliniGRC/GestureRobotController/blob/main/notebook/haoduo/layout.jpg)

Updated Video: https://www.youtube.com/watch?v=hFKa_ChovPw
