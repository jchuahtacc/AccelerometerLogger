#include <ESP8266WiFi.h>
#include "StatusLED.h"

#define MAX_TIMEOUT 30

class WifiWrapper {
public:
  WifiWrapper(int);
  bool wifiConnect(const char*, const char *);
  bool serverConnect(IPAddress, int);
  bool send(void);
protected:

private:
  WiFiClient client;
  StatusLED led = NULL;
//  char response_buffer[200];
};
