# Accelerometer Firmware

The `AccelerometerLogger` folder contains an Arduino/ESP8266 sketch for the Accelerometer firmware. Once you install the Arduino IDE and configure it for use with ESP8266, you may edit the firmware to use your WiFi credentials and set up a station ID.

Find the section of code near the beginnng of `AccelerometerLogger.ino` that looks like this:

``` cpp
// Change these variables to reflect your configuration
const char* ssid = "codetacc";              // your WiFi access point
const char* password = "codetacc";          // your WiFi password
const char* stationId = "codetacc";         // your accelerometer station ID
```

Change the constants inside quotes to reflect your WiFi's SSID (hotspot name) and password. You may leave the `stationId` variable alone, or you can change it to something custom. If you had multiple accelerometers, you could even have them split into different sets of Station IDs, so that they could report to different servers.

Once you verify the sketch, you can upload it to your Accelerometer Logger.