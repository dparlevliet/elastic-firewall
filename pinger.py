#! /usr/bin/python
import os
import sys
import json
import socket
from ext.encryption import Encrypt


def ping(ip, port, salt, api):
  print "Pinging: ", ip, port, salt, api
  command = {
    "api_key": api,
    "area": "ping"
  }
  client_sock = socket.socket()
  client_sock.connect((ip, port))
  client_sock.send(Encrypt(json.dumps(command, separators=(',', ':')), salt))
  client_sock.close()


def main():
  config = json.loads(open('./config.json').read())

  # I hate exec. Keep an eye out for better solutions to this
  exec "from api.%s import Api" % config['server_group']

  api = Api()
  for key in config[config['server_group']]:
    setattr(api, key, config[config['server_group']][key])
  api.grab_servers()

  hostname = socket.gethostname()
  if hostname in config['hostnames']:
    for server in config['hostnames'][hostname]['ping']:
      for ip in api.get_servers(server):
        ping(ip, config['server_port'], config['bsalt'], config['api_key'])


if __name__ == '__main__':
  sys.exit(main())


