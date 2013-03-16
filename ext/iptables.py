"""
@fileoverview IPTables methods
@author David Parlevliet
@version 20130315
@preserve Copyright 2013 David Parlevliet.

IPTables
========
Methods to make dealing with IPTables a little easier.
"""
import subprocess


def default_setup():
  subprocess.Popen("""iptables -P INPUT DROP;
                      iptables -A INPUT -j DROP;""", shell=True)
  loopback_safe()


def loopback_safe():
  subprocess.Popen("iptables -A INPUT -i lo -p all -j ACCEPT", shell=True)
  subprocess.Popen("iptables -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT", shell=True)


def ip_rule(input_type, ip, port, type):
  subprocess.Popen("iptables -%s INPUT -p %s -s %s/%s --dport %s -m state --state NEW,ESTABLISHED -j ACCEPT" %
        (input_type, type, ip, ip, port), shell=True)


def any_rule(input_type, port, type):
  subprocess.Popen("iptables -%s INPUT -p %s -m %s --dport %s -j ACCEPT" %
                      (input_type, type, type, port), shell=True)


def all_new(port, type):
  any_rule('A', port, type)


def all_remove(port, type):
  any_rule('D', port, type)


def ip_new(ip, port, type):
  ip_rule('A', ip, port, type)


def ip_remove(ip, port, type):
  ip_rule('D', ip, port, type)
