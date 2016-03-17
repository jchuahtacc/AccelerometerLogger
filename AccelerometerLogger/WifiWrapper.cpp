#include <ESP8266WiFi.h>
#include "WiFiWrapper.h"
#include "StatusLED.h"

WifiWrapper::WifiWrapper(int ledPin) {
  led = StatusLED(ledPin);
}

bool WifiWrapper::wifiConnect(const char* ssid, const char* password) {
  int times = 0;
  WiFi.begin(ssid, password);
  int status = WiFi.status();
  while (status != WL_CONNECTED && times < MAX_TIMEOUT) {
    switch (status) {
      case WL_NO_SHIELD : Serial.println("Couldn't find WiFi hardware!"); break;
      case WL_NO_SSID_AVAIL : Serial.println("Couldn't find the supplied SSID"); break;
      case WL_CONNECT_FAILED : Serial.println("Couldn't connect to the supplised SSID"); break;
      case WL_IDLE_STATUS : Serial.println("Attempting to connect"); break;
      default : Serial.println("Waiting to connect");
    }
    status = WiFi.status();
    delay(800);
    yield();
    led.pulse(2);
    times++;
  }
  if (status != WL_CONNECTED && times >= MAX_TIMEOUT) {
    return false;
  }
  return true;
}

bool WifiWrapper::serverConnect(IPAddress ip, int port) {
  Serial.println("Attempting to connect client");
  if (!client.connect(ip, port)) return false;
//  memset(response_buffer, 0, 200);
//  Serial.println("Sending hello");
  client.println("Hello!");
  return true;
}

bool WifiWrapper::send(void) {
  if (!client.connected()) return false;
  client.println("Hello!");
  return true;
}

