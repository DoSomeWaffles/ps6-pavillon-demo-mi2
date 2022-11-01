import board
import busio
import adafruit_bmp280
import time 

i2c = busio.I2C(board.SCL, board.SDA)
sensor = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)

while(1):
    print('Temperature: {} degrees C'.format(sensor.temperature)) 
    print('Pressure: {}hPa'.format(sensor.pressure))
    sensor.sea_level_pressure = 1007
    print('Altitude: {} meters'.format(sensor.altitude))
    time.sleep(0.5)