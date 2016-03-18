#include "utility/Adafruit_LIS3DH.h"
#include <Adafruit_Sensor.h>
#include <ESP8266WiFi.h>
#include "StatusLED.h"
#include "WifiWrapper.h"

#define STATUS_LED 0

IPAddress server(192, 168, 1, 101);
int port = 9999;

Adafruit_LIS3DH accel = Adafruit_LIS3DH();
StatusLED status = StatusLED(STATUS_LED);
WifiWrapper wifi = WifiWrapper(STATUS_LED);

// Method prototypes
void commandError(void);
void configError(void);
void configureAccelerometer(void);
void keepAlive(void);

int eventCount = 0;
int flushCount = 0;
long start = 0;

long clientKeepalive = 0;

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
  int command = wifi.getCommand();
  Serial.print("Command: ");
  Serial.println(command);
  switch (command) {
    case COMMAND_CONFIG_ERROR : configError(); break;
    case COMMAND_UNKNOWN : commandError(); break;
    case COMMAND_CONFIGURE : configureAccelerometer(); break;
    case COMMAND_KEEPALIVE : keepAlive(); break;
  }
  delay(700);
  yield();
}

void commandError() {
  Serial.println("Got a bad command from the server");
}

void configError() {
  Serial.println("Got a bad configuration parameter from the server");
}

void configureAccelerometer() {
  Serial.println("Accelerometer configuration requested");
  switch (wifi.requestedRate) {
    case CONFIG_1HZ : Serial.println("Rate 1Hz"); accel.setDataRate(LIS3DH_DATARATE_1_HZ); break;
    case CONFIG_10HZ : Serial.println("Rate 10Hz"); accel.setDataRate(LIS3DH_DATARATE_10_HZ); break;
    case CONFIG_25HZ : Serial.println("Rate 25Hz"); accel.setDataRate(LIS3DH_DATARATE_25_HZ); break;
    case CONFIG_50HZ : Serial.println("Rate 50Hz"); accel.setDataRate(LIS3DH_DATARATE_50_HZ); break;
    case CONFIG_100HZ : Serial.println("Rate 100Hz"); accel.setDataRate(LIS3DH_DATARATE_100_HZ); break;
    case CONFIG_200HZ : Serial.println("Rate 200Hz"); accel.setDataRate(LIS3DH_DATARATE_200_HZ); break;
    case CONFIG_400HZ : Serial.println("Rate 400Hz"); accel.setDataRate(LIS3DH_DATARATE_400_HZ); break;
    default : configError(); break;
  }
  switch (wifi.requestedRange) {
    case CONFIG_2G : Serial.println("Range 2G"); accel.setRange(LIS3DH_RANGE_2_G); break;
    case CONFIG_4G : Serial.println("Range 4G"); accel.setRange(LIS3DH_RANGE_4_G); break;
    case CONFIG_8G : Serial.println("Range 8G"); accel.setRange(LIS3DH_RANGE_8_G); break;
    case CONFIG_16G : Serial.println("Range 16G"); accel.setRange(LIS3DH_RANGE_16_G); break;
    default : configError(); break;
  }
}

void keepAlive() {
  Serial.println("Responding to keepalive request");
  wifi.sendKeepalive();
}

