'''
 Copyright (c) 2021 University of Applied Sciences Western Switzerland / Fribourg

 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 SOFTWARE.

 Project: HEIA-FR / Measure meteorological data for the DEMO_MI2 modular pavillon 

 Purpose: This module is used to measure wind speed. In creates an interface with 
 the RS-485 over USB and communicate with it.

 Author:  Denis Rosset et Julien Piguet
 Date:    Mai 2021
'''

import serial
import time
import Configuration

# method used to set the pressure
# arguments are an integer for the pressure 
def setPressure(pressure):
    try:
        # instantiate the serial communication
        ser = serial.Serial(
            Configuration.ANEMOMETER_SERIAL_PORT,
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            xonxoff=0,
            timeout=5)
        # sending char B to let the anemometer know that we want to calibrate pressure value
        ser.write(b'B')
        while (ser.inWaiting() == 0):
            time.sleep(0.1)
        # read until we can write the value
        serdata = ser.read_until(':')
        # write the value to the anemometer
        ser.write(pressure.encode('utf-8'))
        while (ser.inWaiting() == 0):
            time.sleep(0.1)
        # send a carriage return to validate the calibation
        ser.write('\r'.encode())
        while (ser.inWaiting() == 0):
            time.sleep(0.1)
            time.sleep(0.1)
        ser.close()
        return True
    except Exception as e:
        print(e)
        ser.close()
        return False

# method used to get the wind speed value from the anemometer
def getMeasure():
    try:
        # instantiate the serial communication
        ser = serial.Serial(
            Configuration.ANEMOMETER_SERIAL_PORT,
            baudrate=9600,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            xonxoff=0,
            timeout=5)
        
        # sending char ' ' (space) to let the anemometer know that we want to get the values
        ser.write(b' ')
        while (ser.inWaiting() == 0):
            time.sleep(0.01)
        serdata = ser.readline()
        # decoding the wind speed value as a float
        result = float(serdata.split()[0].decode('UTF-8'))
        ser.close()
        return result
    except Exception as e:
        print(e)
        time.sleep(0.01)
        ser.close()
        return False