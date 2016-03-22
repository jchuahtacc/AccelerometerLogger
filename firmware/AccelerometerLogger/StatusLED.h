#ifndef __STATUSLED_H__
#define __STATUSLED_H__


class StatusLED {
public:
  StatusLED(int);
  void flash();
  void flash(int);
  void pulse(int);
  void blockingError(const char *);
  void on(void);
  void off(void);
protected:
  int ledPin;
};

#endif
