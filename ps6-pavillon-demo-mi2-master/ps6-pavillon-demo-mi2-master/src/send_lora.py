#!/usr/bin/env python3
# V3.0.x firmware

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

 Purpose: This module is used to send the data to LoRa wireless area network

 Author:  Denis Rosset et Julien Piguet
 Date:    Mai 2021
'''

import time, struct, subprocess;
import Configuration
import datetime
import logging
from rak811.rak811_v3 import Rak811

# Send byte to LoRa
# Input: bytesTab (bytes)
# Return: 0 or error message
def send_frame(bytesTab: bytes):
    lora = Rak811()
    logging.info("Configure Lora...")
    lora.set_config('lora:work_mode:0')
    lora.set_config('lora:join_mode:0')
    lora.set_config('lora:region:EU868')
    lora.set_config('lora:app_eui:70B3D50000000000')
    if Configuration.RASPBERRY_PI_ID == 0:
        lora.set_config('lora:app_key:F0ABC0850624B8F884C922560DA5C2B0') # Device 0
    else:
        lora.set_config('lora:app_key:D50268FA6C8566215DEC48B03A1C495D') # Device 1
    lora.set_config('lora:tx_power:0')
    logging.info("Join Lora...")
    lora.join()
    logging.info("Join Success")
    lora.set_config('lora:dr:0')
    logging.info("Send to Lora...")
    lora.send(bytesTab)
    logging.info("Send Success")
    lora.close()
    logging.info("Close Success")
    return 0

# Convert sensors data to bytes and call send lora function
# Input: isTest (bool), timestamp (int), sunIntensity (float), temperature (float), temperatureGlobe (float), humidity (float), windspeed (float), device (int), is_rak (bool)
# Return: 0 or error message
def send_data(isTest: bool, timestamp: int, sunIntensity: float, temperature: float, temperatureGlobe: float, humidity: float, windspeed: float, device = 0, is_rak = True):

    # Convert values into int
    sunIntensityInt: int = int(sunIntensity*100)
    temperatureInt: int = int(temperature*100)
    temperatureGlobeInt: int = int(temperatureGlobe*100)
    humidityInt: int = int(humidity*100)
    windspeedInt: int = int(windspeed*1000)

    # Create control byte
    controlBytes: bytes
    control = 1 # Version
    if isTest:
        control += 128
    if device in {1, 3, 5, 7}:
        control += 16
    if device in {2, 3, 6, 7}:
        control += 32
    if device in {4, 5, 6, 7}:
        control += 64

    controlBytes = bytes([control])

    # Forge byte array
    msg = bytearray(15)
    struct.pack_into('>cIhhhhh', msg, 0, controlBytes, timestamp, sunIntensityInt, temperatureInt, temperatureGlobeInt, humidityInt, windspeedInt)


    msg = bytes(msg)
    logging.info("Send data...")
    hexaOut = ''.join('{:02x}'.format(x) for x in msg)

    # Send data to LoRa (with rak lib or lmic lib)
    if is_rak:
        return send_frame(msg)
    else:
        bashCmd = ["sudo", Configuration.SEND_LORA_EXE_PATH, hexaOut]
        process = subprocess.Popen(bashCmd, stdout=subprocess.PIPE)
        output, error = process.communicate()
        logging.info(process.returncode)
        logging.info(output)
        return process.returncode





# TEST LINE
#send_data(True, int(time.time()), 56.45, 23.12, 24.01, 2.1, 3.2, 0)
