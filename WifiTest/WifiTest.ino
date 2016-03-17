#include <ESP8266WiFi.h>
#include <Esp.h>

const char* ssid = "codetacc";
const char* password = "codetacc";

WiFiClient client;
IPAddress server(146, 6, 176, 201);

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  Serial.println("Hello world");
  WiFi.begin(ssid, password);
  int status = WiFi.status();
  while (status != WL_CONNECTED) {
    switch (status) {
      case WL_NO_SHIELD : Serial.println("Couldn't find WiFi hardware!"); break;
      case WL_NO_SSID_AVAIL : Serial.println("Couldn't find the supplied SSID"); break;
      case WL_CONNECT_FAILED : Serial.println("Couldn't connect to the supplised SSID"); break;
      case WL_IDLE_STATUS : Serial.println("Attempting to connect"); break;
      default : Serial.println("Other status");
    }
    status = WiFi.status();
    delay(200);
  }
  Serial.println("WiFi Connected");
  delay(200);
  if (!client.connect(server, 9999)) {
    Serial.println("Couldn't connect to server");
  }
  Serial.println("Connected to server");
  client.println("blahblahblah");
  while(true) {
    while (client.available()) {
      char c = client.read();
      Serial.print(c);
      yield();
    }
    delay(200);
    yield();
  }
}

void loop() {
  // put your main code here, to run repeatedly:

}
