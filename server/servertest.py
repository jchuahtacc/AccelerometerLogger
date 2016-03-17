#!/bin/python

import SocketServer
import time
from threading import Thread
#from multiprocessing import Process

STATE_DISCONNECTED = 0;
STATE_CONNECTED = 1;
STATE_RUNNING = 2;
STATE_STOPPED = 3;

quit = False

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

class AccelerometerHandler(SocketServer.BaseRequestHandler):
  def handle(self):
    if not (self.request.getpeername()[0] in clients):
        self.client = AccelerometerClient(self.request)
        clients[self.client.ip] = self.client
        print "New client: " + str(self.client.ip)
    while not quit:
        self.data = self.request.recv(1024).strip()
        print "Client data " + self.data
        time.sleep(1)

def print_menu():
    print "(p)rint status"
    print "(s)ignal start"
    print "(h)alt data collection"
    print "(w)rite data to disk"
    print "(q)uit"

if __name__ == "__main__":
  HOST, PORT = "192.168.0.101", 9999
  server = SocketServer.TCPServer((HOST, PORT), AccelerometerHandler)
  t = Thread (target=server.serve_forever)
  t.start()
  quit = False
  try:
    while not quit:
      print_menu()
      choice = raw_input("Enter choice letter: ")
      if choice == "q":
          print "chose quit"
          quit = True
      else:
          print "didnt' choose quit"
    quit = True
    print "Calling server shutdown"
    server.shutdown()
    print "Joining thread"
    t.join()
    print "Goodbye!"
    raise KeyboardInterrupt()
  except KeyboardInterrupt:
    quit = True
    server.shutdown()
    t.join()
    print "Goodbye!"
