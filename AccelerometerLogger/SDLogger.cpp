#include "SDLogger.h"

SDLogger::SDLogger(void) {
  // empty constructor
}

bool SDLogger::begin() {
  return SD.begin(CHIP_SELECT);
//  if (!card.init(SPI_FULL_SPEED, CHIP_SELECT)) return SD_LOGGER_ERROR_READER;
//  if (!volume.init(card)) return SD_LOGGER_ERROR_VOLUME;
//  if (!root.openRoot(volume)) return SD_LOGGER_ERROR_ROOT;
}

bool SDLogger::create() {
  char* data_filename = "DATA0000.CSV";
  char* meta_filename = "DATA0000.TXT";
  char buff[5] = { 0 };
  for (int i = 0; i < 10000; i++) {
    sprintf(buff, "%04i", i);
    memcpy(&data_filename[4], buff, 4);
    memcpy(&meta_filename[4], buff, 4);
    Serial.print("Trying ");
    Serial.print(data_filename);
    Serial.print(", ");
    Serial.println(meta_filename);
    if (!SD.exists(data_filename) && !SD.exists(meta_filename)) {
      datafile = SD.open(data_filename, FILE_WRITE);
      metafile = SD.open(meta_filename, FILE_WRITE);
      return true;
    }
  }
  return false;
}

void SDLogger::log(float x_g, float y_g, float z_g) {
  datafile.print(x_g);
  datafile.print(",");
  datafile.print(y_g);
  datafile.print(",");
  datafile.println(z_g);
}

void SDLogger::finish(void) {
  datafile.flush();
  datafile.close();
}

