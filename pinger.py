#! /usr/bin/python
"""
@fileoverview Ping message sending script
@author David Parlevliet
@version 20130305
@preserve Copyright 2013 David Parlevliet.

Pinger
======
Sends ping messages to all known Elastic Firewall servers
"""
import os
import sys
import json
import socket
import re
from ext.encryption import Encrypt


def ping(ip, port, salt, api):
  print "Pinging: ", ip, port, salt, api
  command = {
    "api_key": api,
    "area": "ping"
  }
  try:
    client_sock = socket.socket()
    client_sock.connect((ip, port))
    client_sock.send(Encrypt(json.dumps(command, separators=(',', ':')), salt))
    client_sock.close()
  except:
    print "Connection refused"
    pass


def main():
  config = json.loads(open('/usr/local/share/elastic-firewall/config.json').read())

  # I hate exec. Keep an eye out for better solutions to this
  exec "from api.%s import Api" % config['server_group']

  try:
    api = Api()
    for key in config[config['server_group']]:
      setattr(api, key, config[config['server_group']][key])
    api.grab_servers()
  except Exception, e:
    print e
    return 1

  hostname = socket.gethostname()
  for c_hostname in config['hostnames']:
    if not re.match(c_hostname, hostname):
      continue
      
    log('Config found at: %s' % c_hostname)
    server_rules = config['hostnames'][c_hostname]
    for server in server_rules['ping']:
      for ip in api.get_servers(server):
        ping(ip, config['server_port'], config['bsalt'], config['api_key'])

  return 0

if __name__ == '__main__':
  sys.exit(main())


