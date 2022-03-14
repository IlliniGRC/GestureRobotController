# Eric Worklog

## Table of Contents

1. [Week 2022-02-07 Finding parts](#2022-02-07-finding-parts)
2. [Week 2022-02-14 Testing Wit-Motion WT901](#2022-02-14-testing-wit-motion-wt901)
3. [Week 2022-03-07 Designing PCB](#2022-03-07-designing-pcb)

## Important Notes

1. [WT901 Manual & Data Sheet](#wt901-manual-and-data-sheet)
2. [WT901 Pinout](#wt901-pinout)
3. [WT901 IIC](#wt901-iic)
4. [Quaternion to Euler](#conversion-from-quaternion-to-euler-angle)
5. [WT901 Operation Environment](#wt901-operation-environment)

## 2022-02-07 Finding Parts

([Back to top](#eric-worklog))

Finding available IMUs

- [Wit-Motion (9-Axis Accelerometer + Tilt Sensor)](https://www.amazon.com/Accelerometer-Acceleration-Gyroscope-Electronic-Magnetometer/dp/B07GBRTB5K?ref_=ast_sto_dp) <- prefer this one
- [Adafruit (9-Axis Accelerometer)](https://www.amazon.com/Adafruit-Absolute-Orientation-Fusion-Breakout/dp/B017PEIGIG/ref=asc_df_B017PEIGIG/?tag=hyprod-20&linkCode=df0&hvadid=312142335725&hvpos=&hvnetw=g&hvrand=10955145127703543807&hvpone=&hvptwo=&hvqmt=&hvdev=c&hvdvcmdl=&hvlocint=&hvlocphy=9022196&hvtargid=pla-442396583748&psc=1)

Finding available STM32 processor

- [STM32F427VGT6](https://www.aliexpress.com/item/1005003731146258.html?spm=a2g0o.productlist.0.0.6f1e5287woZzTa&algo_pvid=ef53fac1-0262-4ef9-8786-5a33670db49b&aem_p4p_detail=2022020920080515995579616864100133835795&algo_exp_id=ef53fac1-0262-4ef9-8786-5a33670db49b-1&pdp_ext_f=%7B%22sku_id%22%3A%2212000026964346600%22%7D&pdp_pi=-1%3B21.0%3B-1%3B-1%40salePrice%3BUSD%3Bsearch-mainSearch) <- STM32F427 chip that have relatively short delivery time (about 2 weeks)

Questions to ask:

- Who will be in charge of soldering bc these CPUs are fragile
- Who will be paying for these components bc they will be expensive

## 2022-02-14 Testing Wit-Motion WT901

([Back to top](#eric-worklog))

### WT901 Manual and Data Sheet

- [WT901 Manual](https://github.com/WITMOTION/WT901/blob/master/WT901%20Manual.pdf)
- [WT901 DataSheet](https://github.com/WITMOTION/WT901/blob/master/WT901%20Datasheet.pdf)

### WT901 Pinout

![WT901 Chip](WT901_chip.png)

**Notice:** The chip uses 5V input voltage, using 3.3V as source voltage might cause IIC communication failure.

The chip uses the `RX` and `TX` pins to communicate with outside with UART protocol. Reading from the sensor through UART is now possible using a naive `uart_read.py` script. Although the IMU have other data to read, now only attempting to read Euler angles and quaternions only.

Testing image

![WT901 UART](WT901_UART.jpg)

The chip can also use the `SCL` and `SDA` pins to communicate with outside with IIC protocol. IIC communication is possible, but the script depends on Arduino right now since it is hard to find and use USB to IIC devices.

### WT901 IIC

**Notice:** Pull-up resistors are needed on `SCL` and `SDA` pins as the documentation specifies because IIC pins are open-drain.

![WT901 IIC_config](WT901_IIC_config.png)

Testing image

![WT901 IIC](WT901_IIC.jpg)

In testing, a Arduino Nano acts like a bridge between computer and WT901 chip.

Thoughts about choosing embedded processor

- A less powerful embedded processor may be used other than STM32F427 at initial thought, the processing of data is not too heavy, even Arduino Nano can handle a few.
- The processor should have ability to communicate through IIC (for WT901), PWM (for vibration motor and LED), and UART (for communicating with bluetooth chip).

### Conversion from quaternion to Euler angle

Source [Wikipedia](https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles#:~:text=cy%3B%0A%0A%20%20%20%20return%20q%3B%0A%7D-,Quaternion%20to%20Euler%20angles%20conversion,-%5Bedit%5D)

    // All angles in radian
    float roll = atan2(2 * (q0 * q1 + q2 * q3), 1 - 2 * (pow(q1, 2) + pow(q2, 2)));
    float pitch = asin(2 * (q0 * q2 - q3 * q1));
    float yaw = atan2(2 * (q0 * q3 + q1 * q2), 1 - 2 * (pow(q2, 2) + pow(q3, 2)));

### Using IIC to communicate with two WT901s

Use two WT901s connected to IIC interface through a extremely long 4-wire ([V+, GND, SDA, SCL]) to test the chip feedback data. This is done to simulated the scenario where the IMUs are mounted on human body.

One of the chips has IIC device address `0x50`, while the other one have IIC device address `0x52` as labeled in the testing diagram.

Testing image

![WT901 IIC two devices](WT901_IIC_two_devices.jpg)

The two devices can respond to IIC inquiries, and they return meaningful data. Testing code is modified to suit usage of multiple chips.

### WT901 Operation Environment

- The chips should be placed away from any magnetic field source (except for Earth's magnetic field of course...). For the magnetometers to stay functional.

  - It should be at least 30cm away from any soft-iron.
  - It should be at least 50cm away from motors.
  - To be added...

## 2022-03-07 Designing PCB

### Type of embedded CPU used

There are two possibilities proposed. First one is use ATMega328P-PU as the main processor, and the other one is using ESP32-WROOM-32D as the main processor. The advantages (+) and disadvantages (-) are listed below for these two processors.

ATMega328P-PU V.S. ESP32-WROOM-32D

- \+ Simple and easier to design a PCB board around. We decided to use a 28DIP package CPU for the ATMega328, since it will be easier when it comes to both designing and soldering the PCB, and it enables us to take the chip out when in situation needed (e.g. flash bootloader, unit testing hardware, etc.)
- \+ Team members are more familiar with this because we have used Arduino boards before. ATMega328P is the exact chip that are used on Arduino UNO and Arduino Nano.
- \- Have less capability of handling calculations, the CPU clock frequency of the ATMega328P is 16MHz (one of the datasheet I found says 20MHz). But it does not matter since the ESP32 can be running at a maximum frequency of 240MHz.
- \- Have less flash size. ATMega328 CPUs usually have a internal flash of 32KB, while the
ESP32 modules have 512KB. This is a huge difference, as when I was writing the test program for driving the SSD1306 OLED display, the driver code will take about 16KB of flash memory, about half of the available space on a ATMega328.
- \- ESP32 chips have built-in WIFI and Bluetooth capability. If an ATMega328 CPU is used, external Bluetooth transceiver will be used either through UART or SPI, which will decrease the efficiency of the system.

The final decision is that I will design two different PCBs, one for the ATMega328, and another one for the ESP32.

Due to the limited internal flash memory available for ATMega328 chips, two processors are required. One is for querying the IMUs and sending out data, and the other one is in charge of running the OLED, buttons, and actuators that belongs to the feedback system. The two chips will communicate through the SPI interface, because there is no other available interfaces on ATMega328 can be used to deliver messages efficiently.

The design that uses ESP32 chip also use two ESP32 modules. It is influenced by the ATMega328 design, the two chips will still divide the jobs into two parts and each one of the processor do its job. However in this case, the two modules are more powerful, and no external Bluetooth modules are needed because both of them have the ability of communication via wireless link using internal hardwares. The communication between the two chips will be using UART instead of SPI for communication since the duplex communication is generally easier when implemented using UART compared to SPI.

### Power system

The power system of two designs of the chips are basically the same, despite the fact that the ATMega328P chips need an input voltage of 5V while the ESP32-WROOM-32D modules only need 3.3V as input voltage. It is because we are trying to use a USB-to-UART chip that operates on 5V input voltage. The name of the chip series is FT232, and we want FT232RL in particular since that is easier to be soldered onto the PCB surface.

The power system have to step-up and regulate the input voltage of the Li-ion battery (about 3.7V $\pm$ 0.3V) to 5V, then supply the FT232RL chip with 5V. So far the designs are the same for both parts.

The next part is supplying voltage to embedded CPUs. With ATmega328, we can directly supply the 5V directly, but for ESP32, we have several choices.

- Because the FT232 chip have a output pin that supplies 3.3V, we can directly power the ESP32 modules using this pin. However, ESP32 chips are known to be hungry in power, and our application will need it to use it full capability, which the FT232 might not have the ability to handle that current.
- Step down the 5V voltage we have stepped up from the Li-ion battery to 3.3V to power the system.
- Build another regulator that connect to the Li-ion battery directly, step-down and regulate the voltage to 3.3V

I choose the second one for now, but it might subject to change during the development stage.

The system is subject to change after we can get the actual chips and able to test them. The USB-to-UART system might be changed if that is too complex to be figured out.

#### 3.7V to 5V Step-up Circuit

![3V7 to 5V](3V7to5VStepup.jpg)

### ESP32 auto-program circuit
