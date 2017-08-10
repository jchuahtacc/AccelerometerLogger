# Setup Instructions for Raspberry Pi Shake Table Controller

### `raspi-config`

```
sudo raspi-config
```

- In `Interfacing Options` enable `SSH`, `SPI` and `I2C`.
- In `Advanced Options` select `Expand Filesystem`
- Reboot

### Installing `jupyter`

```
sudo apt-get install -y python-dev git
sudo pip install --upgrade pip
sudo pip install jupyter
sudo apt-get install -y python-pandas ttf-bistream-vera
```

### Installing the Adafruit Stepper Motor Hat package

```
sudo pip install git+https://github.com/adafruit/Adafruit-Motor-HAT-Python-Library.git
```


