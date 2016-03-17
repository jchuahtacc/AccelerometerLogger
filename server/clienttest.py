#!/bin/python

import socket
import sys

HOST, PORT = "146.6.176.201", 9999
data = "blahblahblah"

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    sock.connect((HOST, PORT))
    sock.sendall(data)

finally:
    sock.close()
