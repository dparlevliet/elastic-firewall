#! /usr/bin/python
import sys
import os
import subprocess


def get_iptables():
  p = subprocess.Popen("iptables -L", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  while(True):
    retcode = p.poll()
    line = p.stdout.readline()
    yield line
    if(retcode is not None):
      break


def filter_iptables(list):
  pass


def main(port, who):
  iptables = filter_iptables(get_iptables())
  # ignore all
  subprocess.Popen("iptables -P INPUT DROP", shell=True)

  # accept all loopback
  subprocess.Popen("iptables -A INPUT -i lo -p all -j ACCEPT", shell=True)
  subprocess.Popen("iptables -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT", shell=True)

  # accept specific from any
  subprocess.Popen("iptables -A INPUT -p tcp -m tcp --dport 22 -j ACCEPT", shell=True)

  # accept specific from ip
  subprocess.Popen("iptables -A INPUT -i eth0 -p tcp -s %s/%s --dport 22"+
                        " -m state --state NEW,ESTABLISHED -j ACCEPT" %
                          (), shell=True)

  # security precaution
  subprocess.Popen("iptables -A INPUT -j DROP", shell=True)


if __name__ == '__main__':
  if len(sys.argv) < 3:
    print "Usage: python update_firewall.py [port] [ip/all]"
    sys.exit(1)
  sys.exit(main(sys.argv[1], sys.argv[2]))