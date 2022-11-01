# Setup LoRa

## Setup Uart
```
sudo raspi-config
```

select option 5 “Interfacing Options” then P6 “Serial” and then select “No” and then “Yes“

```
sudo nano /boot/config.txt
```

Add at the end:
```
dtoverlay=pi3-miniuart-bt
```


## Install rak811 python library
```
sudo apt update

sudo apt upgrade 

sudo apt install python3-pip

sudo pip3 install rak811 
```

## Get DevEui
```
rak811v3 set-config lora:join_mode:0
rak811v3 get-config lora:status | grep DevEui
```