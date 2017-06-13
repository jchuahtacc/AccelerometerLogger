#include <ESP8266WiFi.h>
#include <WiFiUdp.h>
#include "StatusLED.h"

#define MAX_TIMEOUT 30

#define COMMAND_CONFIG_ERROR          -3
#define COMMAND_UNKNOWN               -2
#define COMMAND_DISCONNECTED          -1
#define COMMAND_NONE                  0
#define COMMAND_CONFIGURE             1
#define COMMAND_START                 2
#define COMMAND_HALT                  3
#define COMMAND_KEEPALIVE             4
#define COMMAND_PING                  5

#define OPCODE_CONFIGURE              'r'
#define OPCODE_START                  's'
#define OPCODE_HALT                   'h'
#define OPCODE_KEEPALIVE              'k'     // unused on server side, for now
#define OPCODE_PING                   'p'

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

#define SEND_BUFFER_LENGTH            1024
#define SEND_BUFFER_WATERMARK         990

class WifiWrapper {
public:
  WifiWrapper(int, const char*, const char*);
  bool wifiConnect(const char*, const char *);
  bool wifiConnected(void);
  bool receiveServerInfo(void);
  bool receivedValidServerInfo(void);
  bool serverConnect(void);
  bool serverConnect(IPAddress, int, int);
  bool serverConnected(void);
  bool send(long, int, int, int);
  void sendClientId();
  void flush(void);
  bool sendKeepalive();
  int getCommand(void);
  char requestedRate;
  char requestedRange;
protected:

private:
  WiFiClient client;
  WiFiUDP udp;
  WiFiUDP broadcastListener;
  IPAddress serverIp;
  IPAddress blankIp;
  int controlPort;
  int dataPort;
  StatusLED led = NULL;
  char response_buffer[10];
  char send_buffer[SEND_BUFFER_LENGTH] = { 0 };
  const char* station_id;
  const char* client_id;
  int bufferPosition = 0;
  int writesSinceFlush = 0;
};
