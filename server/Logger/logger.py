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
from IPython.display import display
import socket
import ipywidgets as widgets
import matplotlib.pyplot as plt

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

clients = dict()
sample_count_labels = dict()
status_labels = dict()
milliseconds_label = widgets.Label(value="0", layout=widgets.Layout(width="100%"))

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
            print("New client: ", self.client.clientId)
            try:
                self.request.sendall(str(OPCODE_CONFIGURE + samplerate + samplerange))
            except Exception:
                print("Error configuring new client")
        else:
            self.client = clients[self.request.getpeername()[0]]
            self.client.state = STATE_CONNECTED
            self.client.socket = self.request
            self.client.clientId = self.readClientId()
            print("Client reconnected: " + str(self.client.clientId))
            try:
                self.request.sendall(str(OPCODE_CONFIGURE + samplerate + samplerange))
            except Exception:
                print("Error reconfiguring client upon reconnect")

    def handle(self):
        print("Got a connection!")
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
            print(str(self.client.ip) + " disconnected")
            self.client.state = STATE_DISCONNECTED
            self.request.close()

def broadcast(command, newstate=None):
    for key in clients:
        try:
            client = clients[key]
            client.socket.sendall(command)
            if not newstate is None:
                client.state = newstate
        except Exception:
            print("Error sending command to " + str(client.ip))

def configure():
    global samplerate
    global samplerange
    cmdstring = OPCODE_CONFIGURE + samplerate + samplerange
    broadcast(cmdstring)


def announce(station_id):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', 0))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    data = station_id + "," + str(CONTROL_PORT) + "," + str(DATA_PORT) + "\n"
    s.sendto(data, ('<broadcast>', 9997))


def signal_start():
    broadcast(OPCODE_START, STATE_RUNNING)
    global streamingData
    streamingData = True
    print("Started data collection")
    pass


def halt_data_collection():
    broadcast(OPCODE_HALT, STATE_CONNECTED)
    global streamingData
    streamingData = False
    print("Halted data collection")
    pass


def write_data(filename):
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
    print("Data written to " + filename)
    pass

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

class ThreadedUDPServer(SocketServer.ThreadingMixIn, SocketServer.UDPServer):
    pass

def runServer(host, controlPort, dataPort):
    print "Starting server on " + str(host) + " with control port " + str(controlPort) + " and data port " + str(
        dataPort)
    try:
        controlServer = ThreadedTCPServer((host, controlPort), AccelerometerHandler)
        controlThread = Thread(target=controlServer.serve_forever)
        controlThread.start()
        dataServer = ThreadedUDPServer((host, dataPort), DataStreamHandler)
        dataThread = Thread(target=dataServer.serve_forever)
        dataThread.start()
        quit = False
        controlServer.shutdown()
        dataServer.shutdown()
        controlThread.join()
        dataThread.join()
    except Exception as e:
    	print e


def build_export_panel():
    global clients
    export_text = widgets.Text(
        value="accelerometer.csv"
    )
    export_button = widgets.Button(
        description="Export"
    )
    preview_button = widgets.Button(
        description="Preview"
    )
    def preview_click(b):
        fig,ax = plt.subplots(1)
        fig.show()
        
    preview_button.on_click(preview_click)
    left = widgets.VBox([widgets.Label(value="Filename"), widgets.Label()])
    middle = widgets.VBox([export_text, widgets.Label()])
    right = widgets.VBox([export_button, preview_button])
    export_panel = widgets.HBox([left, middle, right])
    return export_panel
    
def build_status_panel():
    global clients
    global sample_count_labels
    start = widgets.Button(
        description="Start"
    )
    stop = widgets.Button(
        description="Stop"
    )
    col1_children = [ start, stop, widgets.Label() ]
    col2_children = [ widgets.Label() ] * 3
    col3_children = [ widgets.Label(value="Milliseconds", layout=widgets.Layout(width="100%")), widgets.Label(), widgets.Label(value="Status") ]
    col4_children = [ milliseconds_label, widgets.Label(), widgets.Label("Samples")]
    for accel in clients.keys():
        col2_children.append(widgets.Label(value=accel))
        status_labels[accel] = widgets.Label(
            value="CONNECTED",
            layout=widgets.Layout(width="100%")
        )
        col3_children.append(status_labels[accel])
        sample_count_labels[accel] = widgets.Label(
            value="0"
        )
        col4_children.append(sample_count_labels[accel])
    status_panel = widgets.HBox([widgets.VBox(col1_children), widgets.VBox(col2_children), \
                                 widgets.VBox(col3_children), widgets.VBox(col4_children)])
    return status_panel

def build_settings_panel():
    def get_new_value(change):
        if change['type'] == 'change' and change['name'] == 'value':
            return change['new']
        else:
            return None
        
    def rate_setting_change(change):
        global rate
        val = get_new_value(change)
        if val:
            rate = val
            
    def range_setting_change():
        global range
        val = get_new_value(change)
        if val:
            range = val
    
    rate_setting = widgets.Dropdown(
        options = list(zip(["1 Hz", "10 Hz", "25 Hz", "50 Hz", "100 Hz", "200 Hz", "400 Hz"], ["a", "b", "c", "d", "e", "f", "g"])),
        value = samplerate
    )
    rate_setting.observe(rate_setting_change)
    range_setting = widgets.Dropdown(
        options = list(zip(["2 G", "4 G", "8 G", "16 G"], ["a", "b", "c", "d"])),
        value = samplerange
    )
    labels = [widgets.Label(value=x) for x in ["Rate", "Range"]]
    settings = [rate_setting, range_setting]
    label_box = widgets.VBox(labels)
    settings_box = widgets.VBox(settings)
    config_options = widgets.HBox([label_box, settings_box])
    return config_options

def cpanel():
    main_tabs = widgets.Tab()
    main_tabs.children = [ build_status_panel(), build_export_panel(), build_settings_panel() ]
    main_tabs.set_title(0, "Collect Data")
    main_tabs.set_title(1, "Export Data")
    main_tabs.set_title(2, "Settings")
    display(main_tabs)

def configure():
    ipmaybe = ([l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [
             [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in
              [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0])
    interfaces = widgets.Dropdown(
        options = [ipmaybe] if type(ipmaybe) is str else ipmaybe,
        value = ipmaybe if type(ipmaybe) is str else ipmaybe[0],
    )
    cport = widgets.Text(
        value='9999',
        placeholder='Control Port',
        disabled=False
    )
    dport = widgets.Text(
        value='9998',
        placeholder='Data Port',
        disabled=False
    )
    server_id = widgets.Text(
        value='codetacc',
        placeholder='Station ID',
        disabled=False
    )
    header = widgets.Label(
        value='Configure your server',
        layout=widgets.Layout(width='100%')
    )
    go = widgets.Button(
        description='Start server',
        layout=widgets.Layout(width="100%")
    )
    
    left_box = widgets.VBox([ widgets.Label(value=x, disabled=True) for x in ["Interface", "Control Port", "Data Port", "Station ID", ""] ])
    right_box = widgets.VBox([interfaces, cport, dport, server_id, go])
    settings_box = widgets.HBox([left_box, right_box])
    settings_panel = widgets.VBox([header, settings_box])
    def start_clicked(b):
        settings_panel.close()
        #runServer(HOST, CONTROL_PORT, DATA_PORT)
        cpanel()
    go.on_click(start_clicked)
    display(settings_panel)

