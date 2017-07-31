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
from threading import Thread, Lock
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

client_lock = Lock()
ms = 0

sample_count_labels = dict()
status_labels = dict()
milliseconds_label = widgets.Label(value="0", layout=widgets.Layout(width="100%"))

dividers = {"a": 16380, "b": 8192, "c": 4096, "d": 2048}
rates = {"a": "1 Hz", "b": "10 Hz", "c": "25 Hz", "d": "50 Hz", "e": "100 Hz", "f": "200 Hz", "g": "400 Hz"}
ranges = {"a": "2G", "b": "4G", "c": "8G", "d": "16G"}

_main_tabs = None
_status_panel = None
_export_panel = None
_settings_panel = None

class AccelerometerClient(object):
    def __init__(self, socket):
        self.state = STATE_CONNECTED
        self.events = list()
        self.socket = socket
        self.ip = socket.getpeername()[0]
        self.clientId = ""

def chunk(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i + n]

def update_status():
    global miliseconds_label
    global sample_count_labels
    global ms
    milliseconds_label.value = str(ms)
    for _, client in clients.iteritems():
        sample_count_labels[client.clientId].value = str(len(client.events))

class DataStreamHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        global ms
        data = self.request[0].strip()
        if len(data):
            client = clients[self.client_address[0]]
            client.events.extend(chunk(data.split(' '), 5))
            last_event = client.events[-1]
            last_time = int(last_event[1])
            if last_time > ms + 200:
                ms = last_time
                update_status()


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
        print("Client attempting connection")
        global _main_tabs
        global _status_panel
        if not (self.request.getpeername()[0] in clients):
            client_lock.acquire()
            self.client = AccelerometerClient(self.request)
            clients[self.client.ip] = self.client
            self.client.clientId = self.readClientId()
            _status_panel = build_status_panel()
            _main_tabs.children = [ _status_panel, _export_panel, _settings_panel ]
            print(self.client.clientId + " connected")
            try:
                self.request.sendall(str(OPCODE_CONFIGURE + samplerate + samplerange))
            except Exception:
                print("Error configuring new client")
            finally:
                client_lock.release()
        else:
            self.client = clients[self.request.getpeername()[0]]
            self.client.state = STATE_CONNECTED
            self.client.socket = self.request
            self.client.clientId = self.readClientId()
            global status_labels
            status_labels[self.client.clientId].value = STATE_CONNECTED
            print(self.client.clientId + " reconnected")
            try:
                self.request.sendall(str(OPCODE_CONFIGURE + samplerate + samplerange))
            except Exception:
                print("Error reconfiguring client upon reconnect")

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
                        numTimeouts = numTimeouts + 1
                        disconnected = numTimeouts > 5
                    else:
                        disconnected = True

    def finish(self):
        if self.client.ip in clients:
            print(str(self.client.ip) + " disconnected")
            global status_labels
            status_labels[self.client.clientId].value = STATE_DISCONNECTED
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

def broadcast_configure():
    global samplerate
    global samplerange
    cmdstring = OPCODE_CONFIGURE + samplerate + samplerange
    print("Configuring accelerometers with rate " + rates[samplerate] + " and range " + ranges[samplerange])
    broadcast(cmdstring)


def announce(station_id):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(('', 0))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    data = station_id + "," + str(CONTROL_PORT) + "," + str(DATA_PORT) + "\n"
    s.sendto(data, ('<broadcast>', 9997))


def signal_start():
    broadcast(OPCODE_START, STATE_RUNNING)
    global ms
    global streamingData
    ms = 0
    streamingData = True
    print("Started data collection")
    pass


def halt_data_collection():
    broadcast(OPCODE_HALT, STATE_CONNECTED)
    global streamingData
    streamingData = False
    print("Halted data collection")
    pass

def format_event(clientId, event):
    output_arr = [None] * 5
    output_arr[0] = str(clientId)
    output_arr[1] = event[1]
    output_arr[2] = float(event[2]) / dividers[samplerange]
    output_arr[3] = float(event[3]) / dividers[samplerange]
    output_arr[4] = float(event[4]) / dividers[samplerange]
    return output_arr


def write_data(filename):
    if filename.find('.csv') <= -1:
        filename = filename.strip() + '.csv'
    f = open(filename, 'w')
    f.write("clientId,ms,x,y,z")
    f.write("\n")
    for key in clients:
        client = clients[key]
        for event in client.events:
            output_arr = format_event(client.clientId, event)
            outs = [ str(val) for val in output_arr ]
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
    print("Starting server on " + str(host) + " with control port " + str(controlPort) + " and data port " + str(dataPort))
    try:
        controlServer = ThreadedTCPServer((host, controlPort), AccelerometerHandler)
#        controlServer.serve_forever()
        controlThread = Thread(target=controlServer.serve_forever)
        controlThread.start()
        dataServer = ThreadedUDPServer((host, dataPort), DataStreamHandler)
#        dataServer.serve_forever()
        dataThread = Thread(target=dataServer.serve_forever)
        dataThread.start()
        print("Server is listening")
        #controlThread.join()
        #dataThread.join()
    except Exception as e:
        print e

def plot():
    print "Plotting preview..."
    global clients
    f, subplots = plt.subplots(len(clients), 3, sharex='col', sharey='row')
    for i in range(len(clients.keys())):
        client = clients[clients.keys()[i]]
        client_name = client.clientId
        if len(clients) == 1:
            x = subplots[0]
            y = subplots[1]
            z = subplots[2]
        else:
            x = subplots[i][0]
            y = subplots[i][1]
            z = subplots[i][2]
        x.set_title(client_name + " x")
        y.set_title(client_name + " y")
        z.set_title(client_name + " z")
        ms = list()
        x_vals = list()
        y_vals = list()
        z_vals = list()
        for event in client.events:
            scaled = format_event(client.clientId, event)
            ms.append(scaled[1])
            x_vals.append(scaled[2])
            y_vals.append(scaled[3])
            z_vals.append(scaled[4])
        x.scatter(ms, x_vals)
        y.scatter(ms, y_vals)
        z.scatter(ms, z_vals)

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
    def export_click(b):
        write_data(export_text.value)

    def preview_click(b):
        plot()

    export_button.on_click(export_click)
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
    def stop_click(b):
        halt_data_collection()
    def start_click(b):
        signal_start()
    start.on_click(start_click)
    stop.on_click(stop_click)
    col1_children = [ start, stop, widgets.Label() ]
    col2_children = [ widgets.Label() ] * 3
    col3_children = [ widgets.Label(value="Milliseconds", layout=widgets.Layout(width="100%")), widgets.Label(), widgets.Label(value="Status") ]
    col4_children = [ milliseconds_label, widgets.Label(), widgets.Label("Samples")]
    for _, accel in clients.iteritems():
        col2_children.append(widgets.Label(value=accel.clientId))
        status_labels[accel.clientId] = widgets.Label(
            value=accel.state,
            layout=widgets.Layout(width="100%")
        )
        col3_children.append(status_labels[accel.clientId])
        sample_count_labels[accel.clientId] = widgets.Label(
            value=str(len(accel.events))
        )
        col4_children.append(sample_count_labels[accel.clientId])
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
        global samplerate
        val = get_new_value(change)
        if val:
            samplerate = val
            broadcast_configure()

    def range_setting_change():
        global samplerange
        val = get_new_value(change)
        if val:
            samplerange = val
            broadcast_configure()

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
    global _main_tabs
    _main_tabs = widgets.Tab()
    global _status_panel
    global _export_panel
    global _settings_panel
    _status_panel = build_status_panel()
    _export_panel = build_export_panel()
    _settings_panel = build_settings_panel()
    _main_tabs.children = [ _status_panel, _export_panel, _settings_panel ]
    _main_tabs.set_title(0, "Collect Data")
    _main_tabs.set_title(1, "Export Data")
    _main_tabs.set_title(2, "Settings")
    display(_main_tabs)

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
        cpanel()
        announce(server_id.value)
        runServer(interfaces.value, int(cport.value), int(dport.value))

    go.on_click(start_clicked)
    display(settings_panel)

