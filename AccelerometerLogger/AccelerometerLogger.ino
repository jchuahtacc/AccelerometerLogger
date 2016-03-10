#include "SDLogger.h"
#include "Adafruit_LIS3DH.h"
#include <Adafruit_Sensor.h>

#define STATUS_LED 0

// Function prototypes
void readerError(void);
void fileError(void);

SDLogger logger = SDLogger();
Adafruit_LIS3DH accel = Adafruit_LIS3DH();

int eventCount = 0;
int flushCount = 0;
long start = 0;

void setup() {
  pinMode(STATUS_LED, OUTPUT);

  Serial.begin(9600);
  if (!logger.begin()) readerError();
  if (!logger.create()) fileError();
  // the #0 LED is active LOW
  Serial.println("SD initialized");
  if (! accel.begin(0x18)) accelError();
  accel.setRange(LIS3DH_RANGE_4_G);
  digitalWrite(STATUS_LED, LOW);
  start = millis();
}

void loop() {
  if (eventCount < 100) {
    accel.read();
    logger.log(accel.x_g, accel.y_g, accel.z_g);
    eventCount++;
  } else {
    long now = millis();
    Serial.print("time elapsed: " );
    Serial.println(now - start);
    logger.finish();
    finishStatus();
  }
}

void flashStatus() {
  digitalWrite(STATUS_LED, LOW);
  delay(100);
  digitalWrite(STATUS_LED, HIGH);
  delay(100);
}

void readerError() {
  Serial.println("Couldn't connect to SD card reader");
  while (true) {
    for (int i = 0; i < 2; i++) flashStatus();
    delay(1000);
  }
}

void fileError() {
  Serial.println("Couldn't create a data file on the SD card");
  while (true) {
    for (int i = 0; i < 3; i++) flashStatus();
    delay(1000);
  }
}

void accelError() {
  Serial.println("Couldn't initialize accelerometer");
  while (true) {
    for (int i = 0; i < 4; i++) flashStatus();
    delay(1000);
  }
}

void finishStatus() {
  Serial.println("Finished logging.");
  while (true) {
    flashStatus(); flashStatus();
    delay(300);
    flashStatus(); flashStatus();
    delay(1000);
  }
}

