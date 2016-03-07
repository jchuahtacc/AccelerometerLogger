#include "SDLogger.h"

#define STATUS_LED 0

// Function prototypes
void readerError(void);
void volumeError(void);
void rootError(void);


SDLogger logger = SDLogger();

void setup() {
  pinMode(STATUS_LED, OUTPUT);

  Serial.begin(9600);
  int init_result = logger.begin();
  switch(init_result) {
    case SD_LOGGER_ERROR_READER : readerError(); break;
    case SD_LOGGER_ERROR_VOLUME : volumeError(); break;
    case SD_LOGGER_ERROR_ROOT : rootError(); break;
  }
  
  Serial.println("SD card is ready to go");
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

void volumeError() {
  Serial.println("Couldn't read the volume on the SD card");
  while (true) {
    for (int i = 0; i < 3; i++) flashStatus();
    delay(1000);
  }
}

void rootError() {
  Serial.println("Couldn't read the root filesystem on the SD card");
  while (true) {
    for (int i = 0; i < 4; i++) flashStatus();
    delay(1000);
  }
}
