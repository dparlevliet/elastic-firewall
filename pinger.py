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
import time
from ext.encryption import Encrypt

log_path = '/var/log/elastic-firewall/pinger.log'
debug    = True


def log(output):
  output = "[%s] %s" % (time.ctime(), output)
  if debug:
    print output
  open(log_path, 'a').write("\n%s" % output)


def ping(ip, port, salt, api):
  log("Pinging: %s:%s" %  (ip, port))
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
    log("Connection refused")


def main():
  try:
    config = json.loads(open('/usr/local/share/elastic-firewall/config.json').read())
  except Exception, e:
    log("Unable to load config: %s" % e)
    return 1

  # I hate exec. Keep an eye out for better solutions to this
  exec "from api.%s import Api" % config['server_group']

  try:
    api = Api()
    for key in config[config['server_group']]:
      setattr(api, key, config[config['server_group']][key])
    api.grab_servers()
  except Exception, e:
    log("Error: %s" % e)
    return 1

  hostname = socket.gethostname()
  for c_hostname in config['hostnames']:
    if not re.match(c_hostname, hostname):
      continue
      
    log('Config found at: %s' % c_hostname)
    server_rules = config['hostnames'][c_hostname]
    for server in server_rules['ping']:
      for ip in api.get_servers(server):
        ping(ip, server_rules['server_port'], config['bsalt'], config['api_key'])

  return 0

if __name__ == '__main__':
  sys.exit(main())


