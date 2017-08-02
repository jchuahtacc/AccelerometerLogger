#include <ESP8266WiFi.h>
#include "WiFiWrapper.h"
#include "StatusLED.h"
#include <Esp.h>

WifiWrapper::WifiWrapper(int ledPin, const char* stationId, const char* clientId) {
  station_id = stationId;
  client_id = clientId;
  led = StatusLED(ledPin);
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
  udp.begin(PORT);
  return true;
}

int WifiWrapper::parseCommand(void) {
  int numBytes = udp.parsePacket();
  char packetBuffer[512] = { 0 };
  char opcode = ' ';
  char tempRate = ' ';
  char tempRange = ' ';
  if (numBytes) {
    udp.read(packetBuffer, numBytes);
    opcode = packetBuffer[0];
    if (opcode == OPCODE_ANNOUNCE && strstr(packetBuffer, station_id)) {
      serverIp = udp.remoteIP();
      return COMMAND_ANNOUNCE;
    }
    if (!(serverIp == udp.remoteIP())) {
      return COMMAND_UNKNOWN;
    }
    switch (opcode) {
      case OPCODE_KEEPALIVE : return COMMAND_KEEPALIVE; break;
      case OPCODE_START : return COMMAND_START; break;
      case OPCODE_HALT : return COMMAND_HALT; break;
      case OPCODE_CONFIGURE : 
        tempRate = packetBuffer[1];
        tempRange = packetBuffer[2];
        if (tempRate < CONFIG_1HZ || tempRate > CONFIG_400HZ) return COMMAND_CONFIG_ERROR;
        if (tempRange < CONFIG_2G || tempRange > CONFIG_16G) return COMMAND_CONFIG_ERROR; 
        requestedRate = tempRate;
        requestedRange = tempRange;
        return COMMAND_CONFIGURE;
        break;
      case OPCODE_PING : return COMMAND_PING; break;
      default: return COMMAND_UNKNOWN; break;
    }
    return COMMAND_UNKNOWN;    
  }
  return COMMAND_NONE;
}


bool WifiWrapper::wifiConnected() {
  return WiFi.status() == WL_CONNECTED;
}

bool WifiWrapper::serverConnected() {
  return !(serverIp == blankIp);
}

void WifiWrapper::dropServer() {
  serverIp = blankIp;
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

bool WifiWrapper::udp_send(char opcode, const char* data) {
  memset(send_buffer, 0, sizeof send_buffer);
  send_buffer[0] = opcode;
  strcpy(&send_buffer[1], data);
  if (udp.beginPacket(serverIp, PORT)) {
    if (udp.endPacket()) {
      return true;
    } else {
      return false;
    }
  } else {
    return false;
  }
}

void WifiWrapper::sendClientId() {
  memset(send_buffer, 0, sizeof send_buffer);
  send_buffer[0] = RESPONSECODE_CLIENT;
  sprintf(&send_buffer[1], "%s", client_id);
  udp.beginPacket(serverIp, PORT);
  udp.write(send_buffer, strlen(send_buffer));
  udp.endPacket();
  Serial.println("Sent client ID");
}

void WifiWrapper::flush(void) {
  long startFlush = millis();
  /*
  client.println(send_buffer);
  */
  udp.beginPacket(serverIp, PORT);
  udp.write(send_buffer, strlen(send_buffer));
  udp.endPacket();
  
  memset(send_buffer, 0, SEND_BUFFER_LENGTH);
  send_buffer[0] = RESPONSECODE_DATA;
  Serial.print("Flushing ");
  Serial.print(writesSinceFlush);
  Serial.print(" data points for ");
  Serial.print(millis() - startFlush);
  Serial.println("ms");
  writesSinceFlush = 0;
}


