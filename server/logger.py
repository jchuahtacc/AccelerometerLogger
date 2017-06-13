#!/usr/bin/python

# logger.py
#
# Accelerometer Logger server, for configuring and controlling accelerometers
# and then saving the data received
#
# Sample usage:
#
# $ logger.py 192.168.1.100
#
# Starts the logger on the IP address 192.168.1.100 (assuming that's your network
# port's IP address) with the service listening on ports 9999 and 9998
#
# Parameters: ip_address, control_port (default is 9999), data_port (default is 9998)

import SocketServer
import socket
import time
from threading import Thread
import sys

# from multiprocessing import Process

HOST, CONTROL_PORT, DATA_PORT = "192.168.0.100", 9999, 9998

STATE_DISCONNECTED = "DISCONNECTED";
STATE_CONNECTED = "CONNECTED";
STATE_RUNNING = "RUNNING";
STATE_STOPPED = "STOPPED";

OPCODE_CONFIGURE = 'r'
OPCODE_START = 's'
OPCODE_HALT = 'h'
OPCODE_KEEPALIVE = 'k'
OPCODE_PING = 'p'

quit = False
samplerate = "g"
samplerange = "b"
streamingData = False

dividers = {"a": 16380, "b": 8192, "c": 4096, "d": 2048}
rates = {"a": "1 Hz", "b": "10 Hz", "c": "25 Hz", "d": "50 Hz", "e": "100 Hz", "f": "200 Hz", "g": "400 Hz"}
ranges = {"a": "2G", "b": "4G", "c": "8G", "d": "16G"}


class AccelerometerClient(object):
    def __init__(self, socket):
        self.state = STATE_CONNECTED
        self.events = list()
        self.socket = socket
        self.ip = socket.getpeername()[0]
        self.clientId = ""

    def addEvent(self, timestamp, x, y, z):
        event = {"timestamp": timestamp, "x": x, "y": y, "z": z}
        self.events.append(event)


clients = dict()


def chunk(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i + n]


class DataStreamHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        client = clients[self.client_address[0]]
        client.events.extend(chunk(data.split(' '), 5))


class AccelerometerHandler(SocketServer.BaseRequestHandler):
    def readClientId(self):
        clientIdReceived = False
        clientId = ""
        while not clientIdReceived:
            char = self.request.recv(1)
            clientId = clientId + char
            clientIdReceived = char == "\n" or char == "\r"
        return clientId.strip()

    def setup(self):
        if not (self.request.getpeername()[0] in clients):
            self.client = AccelerometerClient(self.request)
            clients[self.client.ip] = self.client
            self.client.clientId = self.readClientId()
            print "New client: ", self.client.clientId
            try:
                self.request.sendall(str(OPCODE_CONFIGURE + samplerate + samplerange))
            except Exception:
                print "Error configuring new client"
        else:
            self.client = clients[self.request.getpeername()[0]]
            self.client.state = STATE_CONNECTED
            self.client.socket = self.request
            self.client.clientId = self.readClientId()
            print "Client reconnected: " + str(self.client.clientId)
            try:
                self.request.sendall(str(OPCODE_CONFIGURE + samplerate + samplerange))
            except Exception:
                print "Error reconfiguring client upon reconnect"

    def handle(self):
        print "Got a connection!"
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
                        numTimeouts = numTimeouts + 1
                        disconnected = numTimeouts > 5
                    else:
                        disconnected = True

    def finish(self):
        if self.client.ip in clients:
            print str(self.client.ip) + " disconnected"
            self.client.state = STATE_DISCONNECTED
            self.request.close()

def ping(ip):
    for key in clients:
        try:
            client = clients[key]
            if client.ip is ip:
                client.socket.sendall(OPCODE_PING)
        except:
            print "Error pinging " + str(client.ip)

def broadcast(command, newstate=None):
    for key in clients:
        try:
            client = clients[key]
            client.socket.sendall(command)
            if not newstate is None:
                client.state = newstate
        except Exception:
            print "Error sending command to " + str(client.ip)


def print_menu():
    print "(a) announce server info"
    print "(c) configure accelerometers"
    print "(p) print status"
    print "(s) start data collection"
    print "(h) halt data collection"
    print "(w) write data to disk"
    print "(l) light up a sensor"
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


def announce():
    station_id = raw_input("What station ID would you like to broadcast? Capitalization matters! ")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', 0))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    data = station_id + "," + str(CONTROL_PORT) + "," + str(DATA_PORT) + "\n"
    s.sendto(data, ('<broadcast>', 9997))


def print_status():
    print "Accelerometer settings - " + ranges[samplerange] + " sampling range at " + rates[samplerate]
    if streamingData:
        print "Currently receiving data"
    else:
        print "Not currently receiving data"
    for key in clients:
        client = clients[key]
        print str(client.ip) + ": " + client.state + " (" + str(len(client.events)) + " events recorded)"
    pass


def signal_start():
    broadcast(OPCODE_START, STATE_RUNNING)
    global streamingData
    streamingData = True
    print "Started data collection"
    pass


def halt_data_collection():
    broadcast(OPCODE_HALT, STATE_CONNECTED)
    global streamingData
    streamingData = False
    print "Halted data collection"
    pass


def write_data():
    filename = raw_input("Enter a filename for the data: ")
    if filename.find('.csv') <= -1:
        filename = filename.strip() + '.csv'
    f = open(filename, 'w')
    f.write("clientId,ms,x,y,z")
    f.write("\n")
    for key in clients:
        client = clients[key]
        for event in client.events:
            event[0] = str(client.clientId)
            event[2] = float(event[2]) / dividers[samplerange]
            event[3] = float(event[3]) / dividers[samplerange]
            event[4] = float(event[4]) / dividers[samplerange]
            outs = [ str(val) for val in event ]
            output = ",".join(outs)
            f.write(output)
            f.write("\n")
        client.events = list()
    f.flush()
    f.close()
    print "Data written to " + filename
    pass

def print_clients():
    import string
    keys = list(clients.keys())
    print "Choose a sensor to signal"
    for i in range(len(keys)):
        print "(" + string.ascii_lowercase[i] + ") " + str(clients[keys[i]].ip)
    choice = raw_input('Enter a choice letter:').lower()
    if choice in string.ascii_lowercase:
        ip = clients[keys[string.ascii_lowercase.index(choice)]].ip
        print "Signalling ", ip
        ping(ip)

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

class ThreadedUDPServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    pass

def runServer(host, controlPort, dataPort):
    print "Starting server on " + str(host) + " with control port " + str(controlPort) + " and data port " + str(
        dataPort)
    try:

        #import socket
        #import thread
        #controlSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #controlSocket.bind(('', controlPort))

        controlServer = ThreadedTCPServer((host, controlPort), AccelerometerHandler)
        controlThread = Thread(target=controlServer.serve_forever)
        controlThread.start()
        dataServer = ThreadedUDPServer((host, dataPort), DataStreamHandler)
        dataThread = Thread(target=dataServer.serve_forever)
        dataThread.start()
        quit = False
        try:
            while not quit:
                print_menu()
                choice = raw_input("Enter choice letter: ").lower()
                if choice == 'a':
                    announce()
                elif choice == 'c':
                    configure()
                elif choice == 'p':
                    print_status()
                elif choice == 's':
                    signal_start()
                elif choice == 'h':
                    halt_data_collection()
                elif choice == 'w':
                    write_data()
                elif choice == 'l':
                    print_clients()
                elif choice == 'q':
                    quit = True
            print "Calling server shutdown"
            controlServer.shutdown()
            dataServer.shutdown()
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
    except Exception as e:
        print "Couldn't start server on the specified IP address and port", e


if __name__ == "__main__":
    if len(sys.argv) > 1:
        HOST = sys.argv[1]
        if len(sys.argv) > 2:
            CONTROL_PORT = int(sys.argv[2])
        if len(sys.argv) > 3:
            DATA_PORT = int(sys.argv[3])
    else:
        # lifted from StackOverflow
        ipmaybe = ([l for l in (
            [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [
                [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in
                 [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0])
        if type(ipmaybe) is str:
            HOST = ipmaybe
            print "Your IP address is " + str(HOST)
        else:
            print "Choose the network interface for this server: "
            current = 1
            for entry in ipmaybe:
                print "(" + str(current) + ") " + entry
                current = current + 1
            choice = raw_input("Choose an entry: ")
            choice = int(choice)
            HOST = ipmaybe[choice - 1]
        cport_input = raw_input("Enter a control port, or leave this blank to use the default of 9999: ")
        if len(cport_input) <= 0:
            CONTROL_PORT = 9999
        else:
            CONTORL_PORT = int(cport_input)
        dport_input = raw_input("Enter a data port, or leave this blank to use the default of 9998: ")
        if len(dport_input) <= 0:
            DATA_PORT = 9998
        else:
            DATA_PORT = int(dport_input)

    runServer(HOST, CONTROL_PORT, DATA_PORT)
