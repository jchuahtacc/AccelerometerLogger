#include "SDLogger.h"

SDLogger::SDLogger(void) {
  // empty constructor
}

int SDLogger::begin() {
  if (!card.init(SPI_FULL_SPEED, CHIP_SELECT)) return SD_LOGGER_ERROR_READER;
  if (!volume.init(card)) return SD_LOGGER_ERROR_VOLUME;
  if (!root.openRoot(volume)) return SD_LOGGER_ERROR_ROOT;
}
