#include "utility/Adafruit_LIS3DH.h"
#include <Adafruit_Sensor.h>
#include <ESP8266WiFi.h>
#include "StatusLED.h"
#include "WifiWrapper.h"

#define STATUS_LED 0

IPAddress server(192, 168, 0, 101);
int port = 9999;

Adafruit_LIS3DH accel = Adafruit_LIS3DH();
StatusLED status = StatusLED(STATUS_LED);
WifiWrapper wifi = WifiWrapper(STATUS_LED);

int eventCount = 0;
int flushCount = 0;
long start = 0;

void setup() {
  pinMode(STATUS_LED, OUTPUT);

  Serial.begin(115200);
  if (!wifi.wifiConnect("codetacc", "codetacc")) {
    status.blockingError(3, "Couldn't connect to WiFi");
  } else {
    Serial.println("Connected to Wifi!");
    Serial.print("Local IP: ");
    Serial.println(WiFi.localIP());
  }
  if (!wifi.serverConnect(server, port)) {
    status.blockingError(4, "Couldn't connect to data server");
  }
  if (!accel.begin(0x18)) {
    status.blockingError(5, "Couldn't find accelerometer");
  }
  accel.setRange(LIS3DH_RANGE_16_G);
  digitalWrite(STATUS_LED, LOW);
  start = millis();
}

void loop() {
  if (!wifi.send()) {
    status.blockingError(6, "Couldn't send data to server");
  }
  delay(700);
  yield();
}
