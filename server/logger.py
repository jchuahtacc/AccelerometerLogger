#!/bin/python

import SocketServer
import socket
import time
from threading import Thread
#from multiprocessing import Process

STATE_DISCONNECTED = 0;
STATE_CONNECTED = 1;
STATE_RUNNING = 2;
STATE_STOPPED = 3;

OPCODE_CONFIGURE = 'r'
OPCODE_START = 's'
OPCODE_HALT = 'h'
OPCODE_KEEPALIVE = 'k'

quit = False
samplerate = "g"
samplerange = "b"
streamingData = False

dividers = { "a" : 16380, "b" : 8192, "c" : 4096, "d" : 2048 }

class AccelerometerClient(object):
    def __init__(self, socket):
        self.state = STATE_CONNECTED
        self.events = list()
        self.socket = socket
        self.ip = socket.getpeername()[0]
    def addEvent(self, timestamp, x, y, z):
        event = { "timestamp" : timestamp, "x" : x, "y" : y, "z": z }
        self.events.append(event)

clients = dict()

def chunk(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

class DataStreamHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        client = clients[self.client_address[0]]
        client.events.extend(chunk(data.split(' '), 5))

class AccelerometerHandler(SocketServer.BaseRequestHandler):
  def setup(self):
    if not (self.request.getpeername()[0] in clients):
        self.client = AccelerometerClient(self.request)
        clients[self.client.ip] = self.client
        print "New client: " + str(self.client.ip)
        try:
            self.request.sendall(str(OPCODE_CONFIGURE + samplerate + samplerange))
        except Exception:
            print "Error configuring new client"
  def handle(self):
    disconnected = False
    numTimeouts = 0
    self.request.settimeout(2)
    while not quit and not disconnected:
        try:
            self.data = self.request.recv(1024).strip()
            if self.data == OPCODE_KEEPALIVE:
                # print "Keep alive"
                self.data = None
                numTimeouts = 0
        except Exception as e:
            if not streamingData:
                if isinstance(e, socket.timeout):
                    print "Timeout counter " + str(numTimeouts)
                    numTimeouts = numTimeouts + 1
                    disconnected = numTimeouts > 5
                else:
                    disconnected = True
  def finish(self):
      if self.client.ip in clients:
          print str(self.client.ip) + " disconnected"
          self.request.close()

def broadcast(command):
    for key in clients:
        try:
            client = clients[key]
            client.socket.sendall(command)
        except Exception:
            print "Error sending command to " + str(client.ip)

def print_menu():
    print "(a) configure accelerometers"
    print "(b) print status"
    print "(c) start data collection"
    print "(d) halt data collection"
    print "(e) write data to disk"
    print "(q) quit"

def configure():
    global samplerate
    global samplerange
    print "Choose a sample rate:"
    print "(a) 1 Hz"
    print "(b) 10 Hz"
    print "(c) 25 Hz"
    print "(d) 50 Hz"
    print "(e) 100 Hz"
    print "(f) 200 Hz"
    print "(g) 400 Hz"
    samplerate = raw_input("Sample rate selection: ").lower()
    print "Choose a sample range:"
    print "(a) 2G"
    print "(b) 4G"
    print "(c) 8G"
    print "(d) 16G"
    samplerange = raw_input("Sample range selection: ").lower()
    pass
    cmdstring = OPCODE_CONFIGURE + samplerate + samplerange
    broadcast(cmdstring)

def print_status():
    pass

def signal_start():
    broadcast(OPCODE_START)
    global streamingData
    streamingData = True
    pass

def halt_data_collection():
    broadcast(OPCODE_HALT)
    global streamingData
    streamingData = False
    pass

def write_data():
    filename = raw_input("Enter a filename for the data: ")
    if filename.find('.csv') <= -1:
        filename = filename.trim() + '.csv'
    f = open(filename, 'w')
    for key in clients:
        client = clients[key]
        for event in client.events:
            event[0] = str(client.ip)
            event[2] = float(event[2]) / dividers[samplerange]
            event[3] = float(event[3]) / dividers[samplerange]
            event[4] = float(event[4]) /dividers[samplerange]
            for item in event:
                f.write(str(item))
                f.write(',')
            f.write('\n')
        client.events = list()
    f.flush()
    f.close()
    pass

if __name__ == "__main__":
  HOST, CONTROL_PORT, DATA_PORT = "192.168.1.108", 9999, 9998
  controlServer = SocketServer.TCPServer((HOST, CONTROL_PORT), AccelerometerHandler)
  controlThread = Thread (target=controlServer.serve_forever)
  controlThread.start()
  dataServer = SocketServer.UDPServer((HOST, DATA_PORT), DataStreamHandler)
  dataThread = Thread(target=dataServer.serve_forever)
  dataThread.start()
  quit = False
  try:
    while not quit:
      print_menu()
      choice = raw_input("Enter choice letter: ").lower()
      if choice == 'a':
        configure()
      elif choice == 'b':
        print_status()
      elif choice == 'c':
        signal_start()
      elif choice == 'd':
        halt_data_collection()
      elif choice == 'e':
        write_data()
      elif choice == 'q':
        quit = True
    print "Calling server shutdown"
    controlServer.shutdown()
    dataSever.shutdown()
    print "Joining thread"
    controlThread.join()
    dataThread.join()
    print "Goodbye!"
    raise KeyboardInterrupt()
  except KeyboardInterrupt:
    quit = True
    controlServer.shutdown()
    dataServer.shutdown()
    controlThread.join()
    dataThread.join()
    print "Goodbye!"
