#!/bin/python

import SocketServer
import time

STATE_DISCONNECTED = 0;
STATE_CONNECTED = 1;
STATE_RUNNING = 2;
STATE_STOPPED = 3;

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
    while True:
        self.data = self.request.recv(1024).strip()
        print "Client data " + self.data
        time.sleep(1)

if __name__ == "__main__":
  HOST, PORT = "192.168.0.101", 9999
  server = SocketServer.TCPServer((HOST, PORT), AccelerometerHandler)
  server.serve_forever()
