#! /usr/bin/python
import os
import sys
import urllib2
import json
import socket
from ext.encryption import Encryption


def ping(ip, port, salt, api):
  command = {
    "api_key": api,
    "area": "ping"
  }
  client_sock = socket.socket()
  client_sock.connect((ip, port))
  client_sock.send(Encrypt(json.dumps(command, separators=(',', ':')), salt))
  client_sock.close()


def main():
  config    = json.loads(open('./config.json').read())

  # I hate exec. Keep an eye out for better solutions to this
  exec "from api.%s import Api" % config['server_group']

  api = Api()
  for key in config[config['server_group']]:
    setattr(api, key, config[config['server_group']][key])
  api.grab_servers()

  hostname  = socket.gethostname()
  hostname  = 'web'
  if hostname in config['hostnames']:
    for ping in config['hostnames'][hostname]:
      for ip in api.get_servers(ping):
        ip = 'locahost'
        ping(ip, config['port'], config['bsalt'], config['api_key'])


if __name__ == '__main__':
  sys.exit(main())


