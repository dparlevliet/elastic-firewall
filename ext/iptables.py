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

current_rules = {}

def rules_list():
  p = subprocess.Popen("iptables --list-rules", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  rules = {}
  for line in iter(p.stdout.readline, b''):
    if len(line) > 0:
      rules[line.replace("\n", '')] = True
  return rules


def allow_all():
  return """iptables -P INPUT ACCEPT;
            iptables -P FORWARD ACCEPT;
            iptables -P OUTPUT ACCEPT;
            iptables -D INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT;"""

def block_all():
  return """iptables -P INPUT DROP;
            iptables -P FORWARD DROP;
            iptables -P OUTPUT ACCEPT;
            iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT;"""


def block_all_on_port(port):
  return "iptables -A INPUT -p tcp --destination-port %s -j DROP" % port


def loopback_safe():
  return """iptables -A INPUT -i lo -j ACCEPT;
            iptables -A OUTPUT -o lo -j ACCEPT"""


def ip_rule(input_type, ip, port, type):
  rule = "iptables -%s INPUT -s %s/%s -p %s -m %s --dport %s -m state --state NEW,ESTABLISHED -j ACCEPT" % \
            (input_type, ip, ip, type, type, port)
  if rule.replace('iptables ', '') in current_rules:
    return None
  return rule


def any_rule(input_type, port, type):
  rule = "iptables -%s INPUT -p %s -m %s --dport %s -j ACCEPT" % \
                      (input_type, type, type, port)
  if rule.replace('iptables ', '') in current_rules:
    return None
  return rule


def all_new(port, type):
  return any_rule('A', port, type)


def all_remove(port, type):
  return any_rule('D', port, type)


def ip_new(ip, port, type):
  return ip_rule('A', ip, port, type)


def ip_remove(ip, port, type):
  return ip_rule('D', ip, port, type)
