#include "StatusLED.h"
#include <Esp.h>

StatusLED::StatusLED(int pin) {
  ledPin = pin;
  pinMode(ledPin, OUTPUT);
}

void StatusLED::flash() {
  on();
  delay(100);
  yield();
  off();
  delay(100);
  yield();
}

void StatusLED::flash(int times) {
  for (int i = 0; i < times; i++) {
    flash();
  }
}

void StatusLED::pulse(int times) {
  for (int i = 0; i < times; i++) {
    flash(); flash();
    delay(300);
    yield();
  }
}

void StatusLED::blockingError(const char * message) {
  Serial.println(message);
  while (true) {
    on();
    delay(800);
    yield();
    off();
    delay(800);
    yield();
  }
}

void StatusLED::on(void) {
  digitalWrite(ledPin, LOW);
}

void StatusLED::off(void) {
  digitalWrite(ledPin, HIGH);
}
