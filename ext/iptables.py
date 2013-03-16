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
import time

current_rules = {}

def rules_list():
  p = subprocess.Popen("iptables --list-rules", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
  rules = {}
  for line in iter(p.stdout.readline, b''):
    if len(line) > 0:
      rules[line.replace("\n", '')] = True
  return rules


def allow_all():
  subprocess.Popen("""iptables -P INPUT ACCEPT;
                      iptables -P FORWARD ACCEPT;
                      iptables -P OUTPUT ACCEPT;
                      iptables -D INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT;""", shell=True)

def block_all():
  subprocess.Popen("""iptables -P INPUT DROP;
                      iptables -P FORWARD DROP;
                      iptables -P OUTPUT ACCEPT;
                      iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT;""", shell=True)


def loopback_safe():
  subprocess.Popen("""iptables -A INPUT -i lo -p all -j ACCEPT;
                      iptables -A INPUT -m state --state RELATED,ESTABLISHED -j ACCEPT""", shell=True)


def ip_rule(input_type, ip, port, type):
  rule = "iptables -%s INPUT -s %s/%s -p %s -m %s --dport %s -m state --state NEW,ESTABLISHED -j ACCEPT" % \
            (input_type, ip, ip, type, type, port)
  if rule.replace('iptables ', '') in current_rules:
    return None
  time.sleep(0.1)
  subprocess.Popen(rule, shell=True)


def any_rule(input_type, port, type):
  rule = "iptables -%s INPUT -p %s -m %s --dport %s -j ACCEPT" % \
                      (input_type, type, type, port)
  if rule.replace('iptables ', '') in current_rules:
    return None
  time.sleep(0.1)
  subprocess.Popen(rule, shell=True)


def all_new(port, type):
  any_rule('A', port, type)


def all_remove(port, type):
  any_rule('D', port, type)


def ip_new(ip, port, type):
  ip_rule('A', ip, port, type)


def ip_remove(ip, port, type):
  ip_rule('D', ip, port, type)
