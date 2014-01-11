"""
@fileoverview Standalone Server
@author David Parlevliet
@version 20140110
@preserve Copyright 2014 David Parlevliet.

Standalone Dedicated Server API
===============================
Class to work for a stand alone dedicated server
"""
import socket
import netifaces
import re

class Api():
  group_name  = "Standalone Server"
  servers     = {}

  def grab_servers(self):
    self.servers[socket.gethostname()] = []
    self.servers[socket.gethostname()].append(netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr'])

  def get_servers(self, name):
    servers = []
    for c_hostname in self.servers:
      servers = servers + (self.servers[c_hostname] if re.match(name, c_hostname) else [])
    return servers

