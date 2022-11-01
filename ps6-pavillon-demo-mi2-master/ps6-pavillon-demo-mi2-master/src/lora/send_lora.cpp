/*******************************************************************************
 * Copyright (c) 2015 Thomas Telkamp and Matthijs Kooijman
 *
 * Permission is hereby granted, free of charge, to anyone
 * obtaining a copy of this document and accompanying files,
 * to do whatever they want with them without any restriction,
 * including, but not limited to, copying, modification and redistribution.
 * NO WARRANTY OF ANY KIND IS PROVIDED.
 *
 * This example sends a valid LoRaWAN packet with payload "Hello,
 * world!", using frequency and encryption settings matching those of
 * the The Things Network.
 *
 * This uses OTAA (Over-the-air activation), where where a DevEUI and
 * application key is configured, which are used in an over-the-air
 * activation procedure where a DevAddr and session keys are
 * assigned/generated for use with all further communication.
 *
 * Note: LoRaWAN per sub-band duty-cycle limitation is enforced (1% in
 * g1, 0.1% in g2), but not the TTN fair usage policy (which is probably
 * violated by this sketch when left running for longer)!

 * To use this sketch, first register your application and device with
 * the things network, to set or generate an AppEUI, DevEUI and AppKey.
 * Multiple devices can use the same AppEUI, but each device has its own
 * DevEUI and AppKey.
 *
 * Do not forget to define the radio type correctly in config.h.
 *
 *******************************************************************************/

#include <stdio.h>
#include <signal.h>
#include <unistd.h>
#include <time.h>
 
#include <lmic.h>
#include <hal/hal.h>

// This EUI must be in little-endian format, so least-significant-byte
// first. When copying an EUI from ttnctl output, this means to reverse
// the bytes. For TTN issued EUIs the last bytes should be 0xD5, 0xB3,0x70.
static const u1_t PROGMEM APPEUI[8]= { 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00 };
void os_getArtEui (u1_t* buf) { memcpy_P(buf, APPEUI, 8);}

// This should also be in little endian format, see above.
static const u1_t PROGMEM DEVEUI[8]= { 0xb4, 0xef, 0x44, 0xf7, 0x57, 0xc4, 0xf9, 0xee };
// Here on Raspi we use part of MAC Address do define devEUI so
// This one above is not used, but you can still old method
// reverting the comments on the 2 following line
void os_getDevEui (u1_t* buf) { memcpy_P(buf, DEVEUI, 8);}
//void os_getDevEui (u1_t* buf) { getDevEuiFromMac(buf); }

// This key should be in big endian format (or, since it is not really a
// number but a block of memory, endianness does not really apply). In
// practice, a key taken from ttnctl can be copied as-is.
// The key shown here is the semtech default key.
static const u1_t PROGMEM APPKEY[16] = { 0x68, 0x24, 0xc9, 0xe7, 0x31, 0x1a, 0x2a, 0xc8, 0x5d, 0xb1, 0x9b, 0x06, 0x5f, 0x06, 0x18, 0x55 };
void os_getDevKey (u1_t* buf) {  memcpy_P(buf, APPKEY, 16);}


// Schedule TX every this many seconds (might become longer due to duty)
// cycle limitations).
const unsigned JOIN_TIMEOUT = 15;

//Flag for Ctrl-C
volatile sig_atomic_t force_exit = 0;
volatile sig_atomic_t is_joining = 0;

int exit_code = 0;

// Dragino Raspberry PI hat (no onboard led)
// see https://github.com/dragino/Lora
#define RF_CS_PIN  RPI_V2_GPIO_P1_22 // Slave Select on GPIO25 so P1 connector pin #22
#define RF_IRQ_PIN RPI_V2_GPIO_P1_07 // IRQ on GPIO4 so P1 connector pin #7
#define RF_RST_PIN RPI_V2_GPIO_P1_11 // Reset on GPIO17 so P1 connector pin #11

// Pin mapping
const lmic_pinmap lmic_pins = { 
    .nss  = RF_CS_PIN,
    .rxtx = LMIC_UNUSED_PIN,
    .rst  = RF_RST_PIN,
    .dio  = {LMIC_UNUSED_PIN, LMIC_UNUSED_PIN, LMIC_UNUSED_PIN},
};

#ifndef RF_LED_PIN
#define RF_LED_PIN NOT_A_PIN  
#endif

void do_send(uint8_t* data) {
    char strTime[16];
    getSystemTime(strTime , sizeof(strTime));
    printf("%s: ", strTime);

    // Check if there is not a current TX/RX job running
    if (LMIC.opmode & OP_TXRXPEND) {
        printf("OP_TXRXPEND, not sending\n");
    } else {
        digitalWrite(RF_LED_PIN, HIGH);
        // Prepare upstream data transmission at the next possible time.
        LMIC_setTxData2(1, data, 15, 0);
        printf("Packet queued\n");
    }
    // Next TX is scheduled after TX_COMPLETE event.
}

void onEvent (ev_t ev) {
    char strTime[16];
    getSystemTime(strTime , sizeof(strTime));
    printf("%s: ", strTime);
 
    switch(ev) {
        case EV_SCAN_TIMEOUT:
            printf("EV_SCAN_TIMEOUT\n");
            force_exit=true;
            exit_code = -1;
        break;
        case EV_BEACON_FOUND:
            printf("EV_BEACON_FOUND\n");
        break;
        case EV_BEACON_MISSED:
            printf("EV_BEACON_MISSED\n");
        break;
        case EV_BEACON_TRACKED:
            printf("EV_BEACON_TRACKED\n");
        break;
        case EV_JOINING:
            printf("EV_JOINING\n");
            is_joining=true;
        break;
        case EV_JOINED:
            printf("EV_JOINED\n");
            is_joining=false;
            digitalWrite(RF_LED_PIN, LOW);
            // Disable link check validation (automatically enabled
            // during join, but not supported by TTN at this time).
            LMIC_setLinkCheckMode(0);
        break;
        case EV_RFU1:
            printf("EV_RFU1\n");
        break;
        case EV_JOIN_FAILED:
            printf("EV_JOIN_FAILED\n");
            force_exit=true;
            exit_code = -1;
        break;
        case EV_REJOIN_FAILED:
            printf("EV_REJOIN_FAILED\n");
            force_exit=true;
            exit_code = -1;
        break;
        case EV_TXCOMPLETE:
            printf("EV_TXCOMPLETE (includes waiting for RX windows)\n");
            if (LMIC.txrxFlags & TXRX_ACK)
              printf("%s Received ack\n", strTime);
            if (LMIC.dataLen) {
              printf("%s Received %d bytes of payload\n", strTime, LMIC.dataLen);
            }
            digitalWrite(RF_LED_PIN, LOW);
            // Schedule next transmission
            //os_setTimedCallback(&sendjob, os_getTime()+sec2osticks(TX_INTERVAL), do_send);
            force_exit=true;
        break;
        case EV_LOST_TSYNC:
            printf("EV_LOST_TSYNC\n");
            force_exit=true;
            exit_code = -1;
        break;
        case EV_RESET:
            printf("EV_RESET\n");
        break;
        case EV_RXCOMPLETE:
            // data received in ping slot
            printf("EV_RXCOMPLETE\n");
        break;
        case EV_LINK_DEAD:
            printf("EV_LINK_DEAD\n");
            force_exit=true;
            exit_code = -1;
        break;
        case EV_LINK_ALIVE:
            printf("EV_LINK_ALIVE\n");
        break;
        default:
            printf("Unknown event\n");
            force_exit=true;
            exit_code = -1;
        break;
    }
}

/* ======================================================================
Function: sig_handler
Purpose : Intercept CTRL-C keyboard to close application
Input   : signal received
Output  : -
Comments: -
====================================================================== */
void sig_handler(int sig)
{
  printf("\nBreak received, exiting!\n");
  force_exit=true;
}

/* ======================================================================
Function: main
Purpose : Send data through LoRa
Input   : command line parameters
Output  : -
Comments: -
====================================================================== */
int main(int argc, char **argv) 
{
    if (argc < 2)
        return -1;


    char *buf = (char*)malloc(15);

    const char *pos = argv[1];


     /* WARNING: no sanitization or error-checking whatsoever */
    for (size_t count = 0; count < 15; count++) {
        sscanf(pos, "%2hhx", &buf[count]);
        pos += 2;
    }

    printf("0x");
    for(size_t count = 0; count < 15; count++)
        printf("%02x", buf[count]);
    printf("\n");


    // caught CTRL-C to do clean-up
    signal(SIGINT, sig_handler);
    
    printf("%s Starting\n", __BASEFILE__);
    
      // Init GPIO bcm
    if (!bcm2835_init()) {
        fprintf( stderr, "bcm2835_init() Failed\n\n" );
        return 1;
    }

	// Show board config
    printConfig(RF_LED_PIN);
    printKeys();

    // Light off on board LED
    pinMode(RF_LED_PIN, OUTPUT);
    digitalWrite(RF_LED_PIN, HIGH);

    // LMIC init
    os_init();
    // Reset the MAC state. Session and pending data transfers will be discarded.
    LMIC_reset();

    // Start job (sending automatically starts OTAA too)
    do_send((uint8_t*)buf);

    ostime_t starttime = os_getTime();

    while(!force_exit) {
        os_runloop_once();
        
        // We're on a multitasking OS let some time for others
        // Without this one CPU is 99% and with this one just 3%
        // On a Raspberry PI 3
        usleep(1000);
        if (is_joining){
            if (starttime + sec2osticks(JOIN_TIMEOUT) < os_getTime()) {
                force_exit = true;
                char strTime[16];
                    getSystemTime(strTime , sizeof(strTime));
                    printf("%s: ", strTime);
                    printf("EV_JOIN_TIMEOUT\n");
                    exit_code = -1;
                }
        }
    }

    // We're here because we need to exit, do it clean

    free(buf);

    // Light off on board LED
    digitalWrite(RF_LED_PIN, LOW);
    
    // module CS line High
    digitalWrite(lmic_pins.nss, HIGH);
    printf( "\n%s, done my job!\n", __BASEFILE__ );
    bcm2835_close();
    return exit_code;
}
