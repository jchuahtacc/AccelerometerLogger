# `logger.py` - The Accelerometer Server

The `server` folder contains a Python script for the Accelerometer logging server. Once you install Python, you may run this script from this folder with the command `python logger.py`. 

### Walkthrough

`logger.py` supports command line options for specifying which IP address the server will bind to and which ports to use, but it will default to detecting your IP address and asking you for a port

```
Your IP address is 10.146.212.254
Enter a control port, or leave this blank to use the default of 9999:
```

Pressing `enter` at this prompt and the next will take you to the main menu:

```
Starting server on 10.146.212.254 with control port 9999 and data port 9998
(a) announce server info
(c) configure accelerometers
(p) print status
(s) start data collection
(h) halt data collection
(w) write data to disk
(q) quit
Enter choice letter:
```

The first step is to power up your Accelerometer. Once it connects to your WiFi network, it will wait for a server announcement with a matching station ID. From `logger.py`, select `a` and enter your station ID.

```
Enter choice letter: a
What station ID would you like to broadcast? Capitalization matters! codetacc
```

At this point, any Accelerometer listening for this station ID will connect automatically and you will see messages. You can use the menu options to configure data frequency and range and print the status of Accelerometers. 

The important options are:

- `(s) start data collection`: triggering data collection for all Accelerometers simultaneously
- `(h) data collection`: halting data collection for all Accelerometers simultaneously
- `(w) write to disk`: Writing all Accelerometer data to a single comma separated file, with the IP address of the Accelerometer that sent the datum