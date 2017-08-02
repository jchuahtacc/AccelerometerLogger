# Accelerometer Server

The Jupyter Notebook [`server.ipynb`](./server.ipynb) allows you to interact with accelerometers.

### Theory of Operation

The notebook and the accelerometers communicate over UDP on port 9999, by default. The connections use keep-alive messages to broadcast their presence. The accelerometers broadcast their client IDs every 2 seconds, while the server broadcasts its station ID every 5 seconds. If the accelerometers do not receive a station ID within a certain amount of time, they consider themselves "timed out" and begin blinking slowly. If the station does not receive a client ID broadcast from a given client within a certain amount of time, it considers the client to be disconnected.

When a user changes the accelerometer rate and range options, starts data collection or stops data collection, the server will broadcast a UDP message for any listening accelerometer. The accelerometer will send UDP packets of data directly to the server when collecting data.
