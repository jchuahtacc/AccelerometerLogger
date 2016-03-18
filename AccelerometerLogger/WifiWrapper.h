#include <ESP8266WiFi.h>
#include "StatusLED.h"

#define MAX_TIMEOUT 30

#define COMMAND_CONFIG_ERROR          -3
#define COMMAND_UNKNOWN               -2
#define COMMAND_DISCONNECTED          -1
#define COMMAND_NONE                  0
#define COMMAND_CONFIGURE             1
#define COMMAND_START                 2
#define COMMAND_HALT                  3

#define OPCODE_CONFIGURE              'r'
#define OPCODE_START                  's'
#define OPCODE_HALT                   'h'

#define CONFIG_1HZ                    'a'
#define CONFIG_10HZ                   'b'
#define CONFIG_25HZ                   'c'
#define CONFIG_50HZ                   'd'
#define CONFIG_100HZ                  'e'
#define CONFIG_200HZ                  'f'
#define CONFIG_400HZ                  'g'

#define CONFIG_2G                     'a'
#define CONFIG_4G                     'b'
#define CONFIG_8G                     'c'
#define CONFIG_16G                    'd'

class WifiWrapper {
public:
  WifiWrapper(int);
  bool wifiConnect(const char*, const char *);
  bool serverConnect(IPAddress, int);
  bool send(void);
  int getCommand(void);
  char requestedRate;
  char requestedRange;
protected:

private:
  WiFiClient client;
  StatusLED led = NULL;
  char response_buffer[10];
};
