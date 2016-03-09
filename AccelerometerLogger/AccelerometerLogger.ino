#include "SDLogger.h"

#define STATUS_LED 0

// Function prototypes
void readerError(void);
void fileError(void);

SDLogger logger = SDLogger();

void setup() {
  pinMode(STATUS_LED, OUTPUT);

  Serial.begin(9600);
  if (!logger.begin()) readerError();
  Serial.println("SD card is ready to go");
  if (!logger.create()) fileError();
  // the #0 LED is active LOW
  digitalWrite(STATUS_LED, LOW);
  delay(3000);
}

void loop() {

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
