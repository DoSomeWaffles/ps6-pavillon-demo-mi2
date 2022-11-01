PYRANOMETER_DIVIDE_NUMBER = 0.00001797

ANEMOMETER_SERIAL_PORT = '/dev/ttyACM0'
# raspberry pi id (0 = interior, 1 = exterior)
RASPBERRY_PI_ID = 0
# raspberry pi hat (False = red hat (C library), True = small hat (python library))
RASPBERRY_PI_IS_PYTHON_HAT = True

DATA_FILE_BEGINNING = "data/data_"
DATA_FILE_FIRST_LINE = "heure de la mesure,intensite (W*m^-2),temperature (Celsius),temperature globe (Celsius),humidite (%),vitesse_du_vent (m*s^-1)"+'\n'

LOG_FILE_NAME = "logs/logs_"

SECONDS_BETWEEN_PRESSURE_UPDATE = 3600
SECONDS_BETWEEN_MEASURES = 1
SECONDS_TO_DATA_LOG = "0"
MINUTES_TO_DATA_SEND = "0,5,10,15,20,25,30,35,40,45,50,55"

LED_INTERVAL_MEASURE = 1
LED_INTERVAL_SAVE = 0.5
LED_INTERVAL_SEND = 0.1
LED_INTERVA_STOPPED = 3

RASPBERRY_PI_SWITCH_GPIO = 21
RASPBERRY_PI_LED_GPIO = 25

SEND_LORA_EXE_PATH = "./lora/send_lora"
LORA_MAX_RETRIES_WHEN_FAILED = 10
LORA_TIME_BETWEEN_RETRIES_SEC = 20
LORA_TIME_BETWEEN_INTERIOR_AND_EXTERIOR_SEC = 30

CONSTANT_DATA_STRUCTURE_INIT_VALUES = {"Rayonnement solaire total": [], "Température": [], "Température globe": [], "Humidité": [], "Vitesse du vent": []}