import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import time

i2c = busio.I2C(board.SCL, board.SDA)

ads = ADS.ADS1115(i2c)
ads.gain = 16

while True:
    chan_delta = AnalogIn(ads, ADS.P0, ADS.P1)
    chan0 = AnalogIn(ads, ADS.P0)
    chan1 = AnalogIn(ads, ADS.P1)
    row = ("C0 : ", chan0.value, " voltage : ", round(chan0.voltage,4), "| C1 : ", chan1.value, " voltage : ", round(chan1.voltage,4), " | Delta : ", chan_delta.value, " voltage : " , round(chan_delta.voltage,10))
    print("{: >4} {: >8} {: >8} {: >8} {: >4} {: >8} {: >8} {: >8} {: >8} {: >8} {: >8} {: >8}".format(*row))
    #row = ("Delta : ", chan_delta.value, " voltage : " , round(chan_delta.voltage,10))
    #print("{: >8} {: >8} {: >8} {: >8}".format(*row))
    time.sleep(1.5)
