#!/usr/bin/python

# logger.py
#
# Accelerometer server helper code

import socketserver
import socket
import time
from threading import Thread, Lock
import sys
from IPython.display import display
import socket
import ipywidgets as widgets
import matplotlib.pyplot as plt

# Configuration options
HOST = b"192.168.8.158"
PORT = 9999
STATION_ID = "codetacc"
PREFER_SUBNET = "192.168"
CLIENT_TIMEOUT = 15000

# State options
STATE_DISCONNECTED = "DISCONNECTED";
STATE_CONNECTED = "CONNECTED";
STATE_RUNNING = "RUNNING";
STATE_STOPPED = "STOPPED";

# Message codes
OPCODE_CONFIGURE = 'r'
OPCODE_START = 's'
OPCODE_HALT = 'h'
OPCODE_KEEPALIVE = 'k'
OPCODE_PING = 'p'
OPCODE_ANNOUNCE = 'a'
RESPONSECODE_CLIENT = 'c'
RESPONSECODE_DATA = 'd'

# Dictionary to contain all client data
clients = dict()

# Dictionary lock
client_lock = Lock()

# Current data collection runtime
ms = 0

# Accelerometer Configuration
samplerate = "g"
samplerange = "b"

# Configuration code dictionary with human readable values
dividers = {"a": 16380, "b": 8192, "c": 4096, "d": 2048}
rates = {"a": "1 Hz", "b": "10 Hz", "c": "25 Hz", "d": "50 Hz", "e": "100 Hz", "f": "200 Hz", "g": "400 Hz"}
ranges = {"a": "2G", "b": "4G", "c": "8G", "d": "16G"}

# UI elements that need global access
sample_count_labels = dict()
status_labels = dict()
milliseconds_label = widgets.Label(value="0", layout=widgets.Layout(width="100%"))
_main_tabs = None
_status_panel = None
_export_panel = None
_settings_panel = None

# UDP Helper functions
def udp_send(ip, data):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    s.connect((ip, PORT))
    s.send(data)
    s.close()

def udp_broadcast(data):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.sendto(data.encode(), (b'<broadcast>', PORT))
    s.close()

def send_configuration(ip):
    udp_send(ip, OPCODE_CONFIGURE + samplerate + samplerange)

# Accelerometer command broadcasts
def broadcast_configure():
    print("Configuring accelerometers with rate " + rates[samplerate] + " and range " + ranges[samplerange])
    udp_broadcast(OPCODE_CONFIGURE + samplerate + samplerange)

def signal_start():
    udp_broadcast(OPCODE_START)
    global ms
    ms = 0
    print("Started data collection")

def halt_data_collection():
    udp_broadcast(OPCODE_HALT)
    print("Halted data collection")
    pass

# Monitor thread that runs broadcasts and checks for timeouts every 5 seconds
class MonitorThread(Thread):
    def __init__(self):
        self.stopped = False
        Thread.__init__(self)

    def run(self):
        while not self.stopped:
            # Announce this station
            udp_broadcast(OPCODE_ANNOUNCE + " " + STATION_ID)

            # Check for timed out clients
            client_lock.acquire()
            for ip, client in clients:
                if time.time() - client.last_announce > CLIENT_TIMEOUT:
                    client.state = STATE_DISCONNECTED
            client_lock.release()

            # Wait 5 seconds
            time.sleep(5)


# Accelerometer Client object that stores connection info, state and client data
class AccelerometerClient(object):
    def __init__(self, ip, clientId):
        self.state = STATE_CONNECTED
        self.events = list()
        self.ip = ip
        self.clientId = clientId
        self.update_announce()

    def update_announce(self):
        self.last_announce = time.time()

    def chunk(self, l, n):
        for i in xrange(0, len(l), n):
            yield l[i:i + n]

    def process_data(self, data):
        global ms
        self.events.extend(self.chunk(data.split(' '), 5))
        last_event = self.events[-1]
        last_time = int(last_event[1])
        self.update_announce()
        if last_time > ms + 200:
            ms = last_time
            update_status()

# UDP listener that responds to packets sent by clients
class AccelUDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        global clients

        # Get a packet
        packet = self.request[0].strip()

        # If the packet has data
        if len(packet):
            client_ip = self.client_address[0]
            # Handle client announcements
            if packet[0] == RESPONSECODE_CLIENT:
                if client_ip not in clients:
                    if client_ip not in clients:
                        client_lock.acquire()
                        clients[client_ip] = AccelerometerClient(client_ip, packet[1:])
                        client_lock.release()
                        _status_panel = build_status_panel()
                        _main_tabs.children = [ _status_panel, _export_panel, _settings_panel ]
                        print(clients[client_ip].clientId + " connected")
                        send_configuration(client_ip)
                    else:
                        clients[client_ip].update_announce()
            # Handle data packets
            elif packet[0] == RESPONSECODE_DATA:
                if client_ip in clients:
                    clients[client_ip].process_data(packet[1:])

# Required mix-in class for threaded UDP server
class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    pass

# Get a list of local interfaces and a good guess as to which interface to use
def get_interfaces():
    global PREFER_SUBNET
    ipmaybe = ([l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1], [
             [(s.connect(('8.8.8.8', 53)), s.getsockname()[0], s.close()) for s in
              [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0])

    ipmaybe = [ipmaybe] if type(ipmaybe) is str else ipmaybe
    if type(ipmaybe) is str:
        default = ipmaybe
    else:
        default = ipmaybe[0]
        for ip in ipmaybe:
            if ip.startswith(PREFER_SUBNET):
                default = ip
    return ipmaybe, default

# Updates UI status during data collection
def update_status():
    global miliseconds_label
    global sample_count_labels
    global ms
    milliseconds_label.value = str(ms)
    for client in clients:
        sample_count_labels[client.clientId].value = str(len(client.events))

# Formats a single client data event for fractions of Gs
def format_event(clientId, event):
    output_arr = [None] * 5
    output_arr[0] = str(clientId)
    output_arr[1] = event[1]
    output_arr[2] = float(event[2]) / dividers[samplerange]
    output_arr[3] = float(event[3]) / dividers[samplerange]
    output_arr[4] = float(event[4]) / dividers[samplerange]
    return output_arr

# Writes client data to CSV
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

# Starts server threads (and user interface)
def start():
    cpanel()
    global HOST
    if HOST is None:
        _, HOST = get_interfaces()
    print("Starting station " + STATION_ID + "  on " + str(HOST) + " with port " + str(PORT))
    try:
        global monitor_thread
        monitor_thread = MonitorThread()
        monitor_thread.start()
        accelServer = ThreadedUDPServer((HOST, PORT), AccelUDPHandler)
        accelThread = Thread(target=accelServer.serve_forever)
        accelThread.start()
        print("Server is listening")
    except Exception as e:
        print(e)

# Outputs a matplotlib preview of client data
def plot():
    print("Plotting preview...")
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

# Builds export panel UI tab
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

# Builds status panel UI tab
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
    for _, accel in clients:
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

# Builds settings panel UI tab
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
    range_setting.observe(range_setting_change)
    labels = [widgets.Label(value=x) for x in ["Rate", "Range"]]
    settings = [rate_setting, range_setting]
    label_box = widgets.VBox(labels)
    settings_box = widgets.VBox(settings)
    config_options = widgets.HBox([label_box, settings_box])
    return config_options

# Shows main user interface
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

# Interactively configure server options before startup
def configure():
    interfaces, default = get_interfaces()
    interfaces = widgets.Dropdown(
        options = interfaces,
        value = default,
    )
    port = widgets.Text(
        value='9999',
        placeholder='Port',
        disabled=False
    )
    server_id_text = widgets.Text(
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

    left_box = widgets.VBox([ widgets.Label(value=x, disabled=True) for x in ["Interface", "Port", "Station ID", ""] ])
    right_box = widgets.VBox([interfaces, port, server_id_text, go])
    settings_box = widgets.HBox([left_box, right_box])
    settings_panel = widgets.VBox([header, settings_box])
    def start_clicked(b):
        settings_panel.close()
        cpanel()
        global STATION_ID
        global HOST
        global PORT

        HOST = interfaces.value
        PORT = int(port.value)
        STATION_ID = server_id_text.value
        start()

    go.on_click(start_clicked)
    display(settings_panel)

