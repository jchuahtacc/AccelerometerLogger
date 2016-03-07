#include <SPI.h>
#include <SD.h>

#define CHIP_SELECT 14
#define CARD_DETECT 12

/************ Error constants ***************
* Returned by begin()
*********************************************/
#define SD_LOGGER_ERROR_READER    -5  // Couldn't connect to SD reader
#define SD_LOGGER_ERROR_VOLUME    -4  // Couldn't open the SD card volume
#define SD_LOGGER_ERROR_ROOT      -3  // Couldn't open the root of the volume
#define SD_LOGGER_ERROR_OK        1   // begin() exited successfully


class SDLogger {
public:
  SDLogger(void);
  int begin();

protected:
  Sd2Card card;
  SdVolume volume;
  SdFile root;
};
