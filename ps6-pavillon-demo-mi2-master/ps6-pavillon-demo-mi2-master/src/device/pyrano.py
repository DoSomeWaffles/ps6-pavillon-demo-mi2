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

 Purpose: This module is used to get the values from the pyranometer via the 
 AC / DC converter

 Author:  Denis Rosset et Julien Piguet
 Date:    Mai 2021
'''


import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import Configuration

# connect to the sensor via I2C
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
# set gain value
ads.gain = 16

# get AC / DC conversion values from the pyranometer via the ads1115 chip
def getRadiationFluxDensity():
    # get delta between P0 and P1 connected wires
    chan_delta = AnalogIn(ads, ADS.P0, ADS.P1)
    # calculate result in watt by square meter 
    result = ((chan_delta.voltage)/ Configuration.PYRANOMETER_DIVIDE_NUMBER)
    # values seems to be not very stable so we clear every values under 0 to be 0
    if result <0:
        result = 0
    return result / ads.gain
