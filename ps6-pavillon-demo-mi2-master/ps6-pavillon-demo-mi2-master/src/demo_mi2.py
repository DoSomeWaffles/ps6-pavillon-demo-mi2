#!/usr/bin/env python3

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

 Purpose: This module is the main module for the application. It measure, saves and 
 send the data from devices connected to itself.

 Author:  Denis Rosset et Julien Piguet
 Date:    Mai 2021
'''

import logging
import time
import sys
import Configuration
from datetime import datetime
import threading
import send_lora
import numpy
import traceback
from statistics import mean
import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library
from apscheduler.schedulers.blocking import BlockingScheduler
# logging system creation to allow to log the import of the other python files
logging.basicConfig(filename=Configuration.LOG_FILE_NAME+str(datetime.now().strftime("%d-%m-%Y_%H-%M-%S"))+".log",format='%(name)-30s: %(levelname)-8s %(asctime)s %(message)s', level=logging.INFO)
print(Configuration.LOG_FILE_NAME+str(datetime.now().strftime("%d-%m-%Y_%H-%M-%S")))
console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(name)-30s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

try:
    from device import mcp9808
    from device import pyrano
    from device import sht31_d
    from device import bmp280
    from device import anemometer
except Exception as e:
    # log when as exception as occured in the import 
    logging.error(repr(e))
    logging.error("Failed to get every sensors, verify i2c connection !")


# global variables instantiation
t0 = time.time()
sem_values_to_log = threading.Semaphore()
sem_values_to_send = threading.Semaphore()
sem_led_interval = threading.Semaphore()
time_before_sending_data = 0
jobs_running = False
led_interval = 1
device_id = 0
python_hat = True
logs_filename = str(datetime.now().strftime("%d-%m-%Y_%H-%M-%S"))
values_to_log = Configuration.CONSTANT_DATA_STRUCTURE_INIT_VALUES
values_to_send = Configuration.CONSTANT_DATA_STRUCTURE_INIT_VALUES
measures_counter = Configuration.SECONDS_BETWEEN_PRESSURE_UPDATE*Configuration.SECONDS_BETWEEN_MEASURES

# method used to get data from every sensors and store it in "values_to_log" and "values_to_send"
def measure_data():
    global measures_counter
    measures_counter+=1
    try:
        #set the pressure to the anemometer
        if(measures_counter>Configuration.SECONDS_BETWEEN_PRESSURE_UPDATE*Configuration.SECONDS_BETWEEN_MEASURES):
            measures_counter=0
            pressure, altitude = bmp280.getPressureAndAltitude()
            if anemometer.setPressure(str(pressure)):
                logging.info("pressure set to anemometer")
            else:
                logging.error("problem while setting pressure to anemometer")

        # get temperature from mcp and temperature and humidity from sht31      
        temp_radiante = mcp9808.getRadiantTemperature()
        temp, humidity = sht31_d.getTemperatureAndHumidity()
    except Exception as e:
        logging.error(repr(e))
        logging.error("error while reading data from i2c, maybe a I2C or RS-485 device is disconnected")
        set_led_interval(20)
        return

    try:
        # get wind speed
        wind_speed = anemometer.getMeasure()
    except Exception as e:
        logging.error("problem while reading wind anemometer")
        wind_speed = -1
    if Configuration.RASPBERRY_PI_ID == 1:
        radiation = 0
    else:
        # get sun intensity level
        radiation = pyrano.getRadiationFluxDensity()

    # update both data structures and store them 
    values_mesured = getValuesToLog()
    values_mesured["Rayonnement solaire total"].append(radiation)
    values_mesured["Température"].append(temp)
    values_mesured["Température globe"].append(temp_radiante)
    values_mesured["Humidité"].append(humidity)
    values_mesured["Vitesse du vent"].append(wind_speed)
    setValuesToLog(values_mesured)

    values_mesured = getValuesToSend()
    values_mesured["Rayonnement solaire total"].append(radiation)
    values_mesured["Température"].append(temp)
    values_mesured["Température globe"].append(temp_radiante)
    values_mesured["Humidité"].append(humidity)
    values_mesured["Vitesse du vent"].append(wind_speed)
    setValuesToSend(values_mesured)

# method called by the scheduler to save the data in a local CSV file
def save_data():
    line = ""
    # getting the values
    temp_values_to_log = getValuesToLog()
    # resetting the data structure
    innitValuesToLog()
    # for each value, add the data to the line
    for data_type in temp_values_to_log:
        try:
            line += ','+str("%.1f" % mean(temp_values_to_log[data_type]))
        except:
            logging.warning("No data to write into file")
            return
    # write values to the file
    log_file = open(Configuration.DATA_FILE_BEGINNING+logs_filename+".csv", "a")
    log_file.write(datetime.now().strftime("%d/%m/%Y %H:%M:%S")+line+"\n")
    log_file.close
    logging.info("measures logged")

# method called by the scheduler to send the data on LoRa
def send_to_lora():
    logging.info("Sending to LoRa...")
    # getting the values
    values = getValuesToSend()
    try:
        radiation = mean(values["Rayonnement solaire total"])
        temp = mean(values["Température"])
        temp_radiante = mean(values["Température globe"])
        humidity = mean(values["Humidité"])
        vitesse_vent = mean(values["Vitesse du vent"])
    except Exception as e:
        logging.warning("No data to send to LoRa")
        print(e)
        return
    # reset the data structure
    innitValuesToSend()
    timestamp = int(datetime.now().timestamp())
    # if the device is 0, the process will wait a certain amount of time so that the two LoRa cards are not sending at the same time
    if device_id==0:
        time.sleep(Configuration.LORA_TIME_BETWEEN_INTERIOR_AND_EXTERIOR_SEC)
    try:
        # try sending to lora
        if send_lora.send_data(False, timestamp, radiation, temp, temp_radiante, humidity, vitesse_vent, device_id, python_hat) is not 0:
            raise CustomError
    except Exception as e:
        logging.error("send failed... trying again in 20 sec")
        counter = 0
        failed = True
        # try sending again to LoRa when the first one failed
        while(counter<Configuration.LORA_MAX_RETRIES_WHEN_FAILED):
            # wait before sending again
            time.sleep(Configuration.LORA_TIME_BETWEEN_RETRIES_SEC)
            try:
                if send_lora.send_data(False, timestamp, radiation, temp, temp_radiante, humidity, vitesse_vent, device_id, python_hat) is 0:
                    failed = False
                    break
                else:
                    logging.error("red hat failed")
                    raise CustomError
            except Exception as e:
                counter += 1
                logging.error("send failed again... trying again in 20 sec")
        if failed:
            logging.error("send failed, giving up sending to LoRa")

# method used to change the led state
def change_led_state(state):
    if(state):
        GPIO.output(Configuration.RASPBERRY_PI_LED_GPIO, GPIO.HIGH)
    else:
        GPIO.output(Configuration.RASPBERRY_PI_LED_GPIO, GPIO.LOW)

# method used to innitialise a new data structure to log
def innitValuesToLog():
    setValuesToLog(Configuration.CONSTANT_DATA_STRUCTURE_INIT_VALUES)

# method used to get the values. It uses a semaphore so there is no concurrency problem
def getValuesToLog():
    sem_values_to_log.acquire()
    res = values_to_log
    sem_values_to_log.release()
    return res

# method used to set the values. It uses a semaphore so there is no concurrency problem
def setValuesToLog(values):
    global values_to_log
    sem_values_to_log.acquire()
    values_to_log = values
    sem_values_to_log.release()

# method used to innitialise a new data structure to send
def innitValuesToSend():
    setValuesToSend(Configuration.CONSTANT_DATA_STRUCTURE_INIT_VALUES)

# method used to get the values. It uses a semaphore so there is no concurrency problem
def getValuesToSend():
    sem_values_to_send.acquire()
    res = values_to_send
    sem_values_to_send.release()
    return res

# method used to set the values. It uses a semaphore so there is no concurrency problem
def setValuesToSend(values):
    global values_to_send
    sem_values_to_send.acquire()
    values_to_send = values
    sem_values_to_send.release()

# method used to prepare the led and call the send_to_lora() and set back the led interval when the send is done
def send_data():
    set_led_interval(0.1)
    send_to_lora()
    set_led_interval(1)

# method used to set the led interval
def set_led_interval(interval):
    sem_led_interval.acquire()
    global led_interval
    led_interval = interval
    sem_led_interval.release()

# method used to make the led blink
def blink_led():
    while(True):
        sem_led_interval.acquire()
        interval = led_interval
        sem_led_interval.release()
        time.sleep(led_interval/2)
        change_led_state(True)
        time.sleep(led_interval/2)
        change_led_state(False)

# method to start the scheduler with the jobs so that he create a new process for each jobs based on the timings 
# defined in the configuraiton file
def start_jobs():
    global sched
    # creating the scheduler and setting the jobs and the timing
    sched = BlockingScheduler()
    send_job = sched.add_job(send_data, 'cron', minute=Configuration.MINUTES_TO_DATA_SEND, max_instances=5)
    save_job = sched.add_job(save_data, 'cron', second=Configuration.SECONDS_TO_DATA_LOG, max_instances=5)
    # start the led blinking thread
    led_thread = threading.Thread(target=blink_led, args=())
    led_thread.daemon = True
    led_thread.start()
    # start the values measurement thread
    measure_thread = threading.Thread(target=sched.start, args=())
    measure_thread.daemon = True
    measure_thread.start()
    jobs_running = True

# method used to wait for the beginning of the second to start the measure to precisely each beginning of second so there is no time shift
def run_measures():
    time.sleep(Configuration.SECONDS_BETWEEN_MEASURES - ((time.time() - t0) % Configuration.SECONDS_BETWEEN_MEASURES))
    measure_data()

# method used at the start of the application to try to connect to the LoRa gateway
def try_lora_connection():
    set_led_interval(0.1)
    # logging infos from the config file
    try:
        logging.info("Device ID (0 is interior and 1 is exterior) "+str(device_id))
        logging.info("Hat used (True = python library and False = C library) "+str(python_hat))
        # trying to send data to LoRa and handeling errors
        if -1 == send_lora.send_data(True, int(datetime.now().timestamp()), -1, -1, -1, -1, -1, device_id, python_hat):
            if not python_hat:
                logging.error("LoRa send error")
            else:
                logging.info("LoRa connection successful")
        return True
    except Exception as e:
        logging.error("lora connexion failed")
        return False
    finally:
        set_led_interval(1)

# class used to throw custom exceptions
class CustomError(Exception):
    pass

# main method used to instantiate devices and GPIOS. it then try the LoRa connection, log the output 
# and start measuring data from devices
def main():
    global device_id
    device_id = Configuration.RASPBERRY_PI_ID
    global python_hat
    python_hat = Configuration.RASPBERRY_PI_IS_PYTHON_HAT
    GPIO.setwarnings(False)
    GPIO.setup(Configuration.RASPBERRY_PI_SWITCH_GPIO, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(Configuration.RASPBERRY_PI_LED_GPIO, GPIO.OUT)
    # writing the first line of the CSV file
    log_file = open(Configuration.DATA_FILE_BEGINNING+logs_filename+".csv", "a")
    log_file.write(Configuration.DATA_FILE_FIRST_LINE)
    log_file.close()
    t0 = time.time()
    if try_lora_connection():
        logging.info("Connection with LoRa Sucessful")
    else:
        logging.error("Failed LoRa Connexion, continuing...")
    start_jobs()
    button_is_pushed = False
    # main while for the program, it nevers stops. It logs a warning when the button is not pushed
    while True:
        if GPIO.input(Configuration.RASPBERRY_PI_SWITCH_GPIO) == GPIO.HIGH:
            if not button_is_pushed:
                set_led_interval(1)
                logging.info("button pushed, starting measures...")
                button_is_pushed=True
            # measure data from devices
            run_measures()
        else:
            button_is_pushed = False
            logging.warning("button is not pushed...")
            set_led_interval(Configuration.LED_INTERVA_STOPPED)
            time.sleep(5)

# call the main function as entry point of program
if __name__ == "__main__":
    main()