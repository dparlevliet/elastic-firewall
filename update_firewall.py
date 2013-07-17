#! /usr/bin/python
"""
@fileoverview Update iptables firewall rules
@author David Parlevliet
@version 20130706
@preserve Copyright 2013 David Parlevliet.

Update Firewall
===============
This script will read the config file, contact the API for server information,
and then update the iptables rules list.
"""
import sys
import os
import json
import pickle
import socket
import ext.iptables as ipt
import re
import fcntl
import subprocess
import time
from copy import copy


app_path    = '/usr/local/share/elastic-firewall'
pid_path    = '/var/run/elastic-firewall-update.pid'
log_path    = '/var/log/elastic-firewall/firewall.log'
rules_path  = '/var/log/elastic-firewall/rules.pickle'

debug    = False
api      = None


def log(output):
  output = "[%s] %s" % (time.ctime(), output)
  if debug:
    print output
  open(log_path, 'a').write("\n%s" % output)


class ElasticRules():
  restarted = False
  rules = {
    'uptime': 0,
    'allowed_ips': {},
    'ports': {},
  }

  def __init__(self):
    ipt.current_rules = ipt.rules_list()

  def build_port_rule_key(self, port, whom, type):
    key = "%s:%s:%s" % (port, type, whom)
    return key

  def add_port_rule(self, port, whom, type):
    key = self.build_port_rule_key(port, whom, type)
    self.rules['ports'][key] = (port, whom, type, True)

  def remove_port_rule(self, port, whom, type):
    key = self.build_port_rule_key(port, whom, type)
    if key not in self.rules['ports']:
      return None
    self.rules['ports'][key] = (port, whom, type, False)

  def add_allowed_ip(self, ip):
    self.rules['allowed_ips'][ip] = True

  def remove_allowed_ip(self, ip):
    self.rules['allowed_ips'][ip] = False

  def load(self):
    try:
      self.rules = pickle.loads(open(rules_path).read())
      self.loaded_rules = copy(self.rules)

      # backwards compatability assurance
      if 'uptime' not in self.rules:
        self.rules['uptime'] = 0

    except:
      pass

  def save(self):
    for ip, allowed in copy(self.rules['allowed_ips']).iteritems():
      if not allowed:
        del self.rules['allowed_ips'][ip]

    return open(rules_path, 'w').write(pickle.dumps(self.rules))

  def split_multiline_rules(self, rules):
    new_rules = []
    for rule in rules.split("\n"):
      new_rules.append(rule.lstrip().replace(';', ''))
    return new_rules

  def update_firewall(self, server_rules):
    rules = []

    try:
      if 'block_all' not in server_rules:
        server_rules['block_all'] = False

      if (server_rules['block_all'] == True \
            and 'block_all_assigned' not in self.rules) \
            or self.restarted == False:
        log('Blocking all incoming connections.')
        rules = rules + self.split_multiline_rules(ipt.block_all())
        self.rules['block_all_assigned'] = True
        del self.rules['allow_all_assigned']

      elif (server_rules['block_all'] == False \
            and 'allow_all_assigned' not in self.rules) \
            or self.restarted == True:
        log('Allowing all incoming connections.')
        rules = rules + self.split_multiline_rules(ipt.allow_all())
        self.rules['allow_all_assigned'] = True
        del self.rules['block_all_assigned']
    except KeyError:
      pass

    for key, rule in self.rules['ports'].iteritems():
      if len(rule) < 4:
        self.rules['ports'][key] = rule + (True,)
        rule = rule + (True,)
      apply_rule = rule[3]

      # no restriction on this port, anyone can connect.
      if rule[1] == 'all':
        if apply_rule:
          rules.append(ipt.all_new(rule[0], rule[2]))
        else:
          rules.append(ipt.remove_new(rule[0], rule[2]))

      # restrict port to all servers in the allowed list
      elif rule[1] == 'allowed':
        for ip in self.rules['allowed_ips']:
          if self.rules['allowed_ips'][ip] == True and apply_rule:
            rules.append(ipt.ip_new(ip, rule[0], rule[2]))
          else:
            rules.append(ipt.ip_remove(ip, rule[0], rule[2]))

      # restrict port to certain servers
      elif type(rule[1]) == list:
        for host in rule[1]:
          for ip in api.get_servers(host):
            if apply_rule:
              rules.append(ipt.ip_new(ip, rule[0], rule[2]))
            else:
              rules.append(ipt.ip_remove(ip, rule[0], rule[2]))

      if not rule[1] == 'all' and server_rules['block_all'] == False:
        rules.append(ipt.block_all_on_port(rule[0]))

    if 'loopback_assigned' not in self.rules:
      # internal network must be able to access outside world
      rules = rules + self.split_multiline_rules(ipt.loopback_safe())
      self.rules['loopback_assigned'] = True

    log('Applying rules:')
    return [(None if debug else subprocess.Popen(
      rule.split(' '), 
      stdout=subprocess.PIPE, 
      stderr=subprocess.PIPE
    ), log(rule)) for rule in rules if not rule == None]


def main(argv):
  global debug, api

  # Parse passed arguments.
  for arg in argv:
    # Test mode will only output iptable commands. No commands will be run.
    # https://github.com/dparlevliet/elastic-firewall/issues/9
    if arg.lower() == '--test-mode':
      debug = True

  log("Lock the process so we do not double up running tasks.")
  pid = open(pid_path, 'w')
  try:
    fcntl.lockf(pid, fcntl.LOCK_EX | fcntl.LOCK_NB)
  except IOError:
    log("Elastic firewall is already running an update.")
    return 1

  rules = ElasticRules()

  log('Loading any previous rules.')
  rules.load()

  # check server uptime to see if it's been restarted since last check
  with open('/proc/uptime', 'r') as f:
    uptime_seconds = float(f.readline().split()[0])
    uptime_seconds = 0
    if uptime_seconds < rules.rules['uptime']:
      rules.restarted = True
    rules.rules['uptime'] = uptime_seconds

  log('Loading config.')
  try:
    config = json.loads(open('%s/config.json'%app_path).read())
  except:
    log("Cannot load config file.")
    return 1

  # I hate exec. Keep an eye out for better solutions to this
  exec "from api.%s import Api" % config['server_group']

  log('Grabbing servers from the API.')
  try:
    api = Api()
    for key in config[config['server_group']]:
      setattr(api, key, config[config['server_group']][key])
    api.grab_servers()
  except Exception, e:
    log(e)
    return 1

  found_ips = []
  hostname  = socket.gethostname()
  server_rules = None

  log('Trying to find the config for this server.')
  for c_hostname in config['hostnames']:
    if not re.match(c_hostname, hostname):
      continue

    log('Config found at: %s' % c_hostname)
    server_rules = config['hostnames'][c_hostname]
    for server in server_rules['allow']:
      for ip in api.get_servers(server):
        rules.add_allowed_ip(ip)
        found_ips.append(ip)

  # this server isn't in the config
  if not server_rules:
    log('Could not find a config file for this server')
    return 0

  # Add any defined safe IPs so the list of firewall rules list.
  for ip in server_rules['safe_ips']:
    rules.add_allowed_ip(ip)
    found_ips.append(ip)

  # Assign all our port rules to the firewall rules list.
  for port_rule in server_rules['firewall']:
    rules.add_port_rule(*port_rule)

  # Remove any open ports that might have been removed from config
  for e_key, e_rule in copy(rules.rules['ports']).iteritems():
    e_rule = list(e_rule)
    for rule in server_rules['firewall']:
      if not e_rule[0] == rule[0]:
        continue

      if len(e_rule) == 4:
        del e_rule[3]

      key = rules.build_port_rule_key(*rule)
      if key not in rules.rules['ports'] or not e_rule == rule:
        log("Removing port rule: %s:%s:%s" % tuple(e_rule))
        rules.remove_port_rule(*e_rule)

  # Remove any ips that are no longer part of the network
  for ip in copy(rules.rules['allowed_ips']):
    if ip not in found_ips:
      rules.remove_allowed_ip(ip)

  # This server is acting as a ping server too, we must open the port.
  # https://github.com/dparlevliet/elastic-firewall/issues/1
  if server_rules['server'] == True:
    rules.add_port_rule(server_rules['server_port'], 'all', 'tcp')

  rules.update_firewall(server_rules)
  if not debug:
    rules.save() # save the rules for comparison later
  os.unlink(pid_path)
  log('Complete.')
  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv))
