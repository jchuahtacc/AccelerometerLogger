#include <ESP8266WiFi.h>
#include "WiFiWrapper.h"
#include "StatusLED.h"
#include <Esp.h>

WifiWrapper::WifiWrapper(int ledPin, const char* stationId) {
  station_id = stationId;
  led = StatusLED(ledPin);
  controlPort = -1;
  dataPort = -1;
  blankIp = IPAddress(0, 0, 0 ,0);
  serverIp = blankIp;
}

bool WifiWrapper::wifiConnect(const char* ssid, const char* password) {
  int times = 0;
  WiFi.begin(ssid, password);
  int status = WiFi.status();
  while (!wifiConnected() && times < MAX_TIMEOUT) {
    switch (status) {
      case WL_NO_SHIELD : Serial.println("Couldn't find WiFi hardware!"); break;
      case WL_NO_SSID_AVAIL : Serial.println("Couldn't find the supplied SSID"); break;
      case WL_CONNECT_FAILED : Serial.println("Couldn't connect to the supplied SSID"); break;
      case WL_IDLE_STATUS : Serial.println("Attempting to connect to WiFi"); break;
      default : Serial.println("Attempting to connect to WiFi");
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
  Serial.println("WiFi Connected!");

  // Start UDP listener  
  return true;
}

bool WifiWrapper::receivedValidServerInfo(void) {
  return controlPort > 0 && dataPort > 0 && !(serverIp == blankIp);
}

bool WifiWrapper::receiveServerInfo(void) {
  broadcastListener.begin(9997);
  char packetBuffer[512] = { 0 };
  bool received = false;
  int numBytes = 0;
  while (!received) {
    numBytes = broadcastListener.parsePacket();
    if (numBytes) {
      broadcastListener.read(packetBuffer, numBytes);
      if (strstr(packetBuffer, station_id)) {
        char* p = strchr(packetBuffer, ',') + 1;
        int receivedControlPort = atoi(p);
        p = strchr(p, ',') + 1;
        int receivedDataPort = atoi(p);
        if (receivedDataPort > 0 && receivedControlPort > 0) {
          serverIp = broadcastListener.remoteIP();
          controlPort = receivedControlPort;
          dataPort = receivedDataPort;
          Serial.print("IP: ");
          Serial.println(serverIp);
          Serial.print("Control Port: ");
          Serial.println(controlPort);
          Serial.print("Data Port: ");
          Serial.println(dataPort);
          received = true;
          return true;
        }
      }
    }
    led.on();
    delay(500);
    yield();
    led.off();
    delay(500);
    yield();
  }
}

bool WifiWrapper::wifiConnected() {
  return WiFi.status() == WL_CONNECTED;
}

bool WifiWrapper::serverConnect() {
  Serial.println("Attempting to connect to server");
  if (!client.connect(serverIp, controlPort)) return false;
//  memset(response_buffer, 0, 200);
//  Serial.println("Sending hello");
//  client.println("Hello!");
  Serial.println("Server connected!");
  return true;  
}

bool WifiWrapper::serverConnect(IPAddress ip, int cport, int dport) {
  serverIp = ip;
  controlPort = cport;
  dataPort = dport;
  return serverConnect();
}

bool WifiWrapper::serverConnected() {
  return client.connected();
}

bool WifiWrapper::sendKeepalive(void) {
  if (!serverConnected()) return false;
  client.println(OPCODE_KEEPALIVE);
  return true;
}

bool WifiWrapper::send(long timestamp, int x, int y, int z) {
  writesSinceFlush++;
  if (!serverConnected()) return false;
  int currentLength = strlen(send_buffer);
  send_buffer[currentLength] = 'e';
  send_buffer[currentLength + 1] = ' ';
  sprintf(&send_buffer[currentLength + 2], "%lu", timestamp);
  currentLength = strlen(send_buffer);
  send_buffer[currentLength] = ' ';
  sprintf(&send_buffer[currentLength + 1], "%i", x);
  currentLength = strlen(send_buffer);
  send_buffer[currentLength] = ' ';
  sprintf(&send_buffer[currentLength + 1], "%i", y);
  currentLength = strlen(send_buffer);
  send_buffer[currentLength] = ' ';
  sprintf(&send_buffer[currentLength + 1], "%i", z);
  currentLength = strlen(send_buffer);
  send_buffer[currentLength] = ' ';
  if (strlen(send_buffer) >= SEND_BUFFER_WATERMARK) {
    flush();
  }
  return true;
}

void WifiWrapper::flush(void) {
  long startFlush = millis();
  /*
  client.println(send_buffer);
  */
  udp.beginPacket(serverIp, dataPort);
  udp.write(send_buffer, strlen(send_buffer));
  udp.endPacket();
  
  memset(send_buffer, 0, SEND_BUFFER_LENGTH);
  Serial.print("Flushing ");
  Serial.print(writesSinceFlush);
  Serial.print(" data points for ");
  Serial.print(millis() - startFlush);
  Serial.println("ms");
  writesSinceFlush = 0;
}

int WifiWrapper::getCommand(void) {
  if (!serverConnected()) return COMMAND_DISCONNECTED;
  if (!client.available()) return COMMAND_NONE;
  char opcode = client.read();
  // Serial.print("Opcode: " );
  // Serial.println(opcode);
  switch (opcode) {
    case OPCODE_KEEPALIVE : return COMMAND_KEEPALIVE; break;
    case OPCODE_START : return COMMAND_START; break;
    case OPCODE_HALT : return COMMAND_HALT; break;
    case OPCODE_CONFIGURE : 
      // Serial.println("Checking OPCODE_CONFIGURE");
      if (!client.available()) return COMMAND_CONFIG_ERROR; 
      if (!(client.peek() >= CONFIG_1HZ && client.peek() <= CONFIG_400HZ)) return COMMAND_CONFIG_ERROR;
      requestedRate = client.read();
      if (!(client.peek() >= CONFIG_2G && client.peek() <= CONFIG_16G)) return COMMAND_CONFIG_ERROR; 
      requestedRange = client.read();
      return COMMAND_CONFIGURE;
      break;
    default: return COMMAND_UNKNOWN; break;
  }
  return COMMAND_UNKNOWN;
}

