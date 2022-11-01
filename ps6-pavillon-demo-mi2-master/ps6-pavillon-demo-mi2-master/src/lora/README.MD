# Setup send_lora

## Install raspi-lmic

**1st step:**
You need 3 dependencies:
- build essential package `apt-get install build-essential`
- other tools packages `apt-get install git-core wget`
- [bcm2835_library](http://www.airspayce.com/mikem/bcm2835/):
  ```
  # download the latest version of the library (for example):
  wget http://www.airspayce.com/mikem/bcm2835/bcm2835-1.69.tar.gz
  # then:
  tar zxvf bcm2835-1.69.tar.gz
  cd bcm2835-1.69
  ./configure
  make
  sudo make check
  sudo make install
  # and very important
  sudo reboot now
  ```

**2nd step:**
Clone branch repository
```shell
git clone https://github.com/pmanzoni/raspi-lmic.git
```



## Makefile
Edit the LMICBASE path to the raspi-lmic/src library

Example:

```Makefile
LMICBASE = /home/pi/src/lora/raspi-lmic/src
```

## Configure LoRa EUI

DEVEUI and APPKEY must be edited. They can be retrieved from the chirpstack server.

**DEVEUI**: This EUI must be in little-endian format
```C
static const u1_t PROGMEM DEVEUI[8]= { 0xb4, 0xef, 0x44, 0xf7, 0x57, 0xc4, 0xf9, 0xee };
```

**APPKEY**: This EUI must be in big-endian format
```C
static const u1_t PROGMEM APPKEY[16] = { 0x68, 0x24, 0xc9, 0xe7, 0x31, 0x1a, 0x2a, 0xc8, 0x5d, 0xb1, 0x9b, 0x06, 0x5f, 0x06, 0x18, 0x55 };
```

## Compiling

Clean install
```Bash
make clean
```

Compile
```Bash
make
```

The program should be call with a parameter, a hexadecimal string representing 15 bytes