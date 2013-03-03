#! /usr/bin/python
import sys
import json
import socket


def main():
  client_sock = socket.socket()
  client_sock.connect(('eddie-node-server', 9957))
  client_sock.send(Encrypt(json.dumps(command, separators=(',', ':')), 'M2U3YTAzMTgxYTBmMkODQzQkMZDdkMWE'))
  client_sock.close()


if __name__ == '__main__':
  sys.exit(main())


