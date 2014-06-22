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

debug       = False
api         = None


def log(output):
  output = "[%s] %s" % (time.ctime(), output)
  if debug:
    print output
  if not os.path.exists(os.path.dirname(log_path)):
    os.makedirs(os.path.dirname(log_path))
  open(log_path, 'a+').write("\n%s" % output)


class ElasticRules():
  restarted = False
  current_rules = {}
  rules = {
    'uptime': 0,
    'allowed_ips': {},
    'ports': {},
  }

  def __init__(self):
    self.current_rules = ipt.rules_list()
    log('<<< Found existing rules:')
    for rule in self.current_rules:
      log(rule)
    log('<<< End')

  def build_port_rule_key(self, port, whom, type):
    key = "%s:%s:%s" % (port, type, whom)
    return key

  def add_port_rule(self, port, whom, type):
    log(">>> Added port rule [%s, %s, %s]" % (port, whom, type))
    key = self.build_port_rule_key(port, whom, type)
    self.rules['ports'][key] = (port, whom, type, True)

  def remove_port_rule(self, port, whom, type):
    log(">>> Removed port rule [%s, %s, %s]" % (port, whom, type))
    key = self.build_port_rule_key(port, whom, type)
    if key not in self.rules['ports']:
      return None
    self.rules['ports'][key] = (port, whom, type, False)

  def add_allowed_ip(self, ip):
    log(">>> Added ip to allowed list: %s" % ip)
    self.rules['allowed_ips'][ip] = True

  def remove_allowed_ip(self, ip):
    log(">>> Removed ip from allowed list: %s" % ip)
    self.rules['allowed_ips'][ip] = False

  def load(self):
    try:
      self.rules = pickle.loads(open(rules_path).read())
      self.loaded_rules = copy(self.rules)

      # backwards compatability assurance
      if 'uptime' not in self.rules:
        self.rules['uptime'] = 0

    except:
      log("<<< Unexpected error loading previous rules")
      pass

  def save(self):
    for ip, allowed in copy(self.rules['allowed_ips']).iteritems():
      if not allowed:
        del self.rules['allowed_ips'][ip]

    if not os.path.exists(os.path.dirname(rules_path)):
      os.makedirs(os.path.dirname(rules_path))
    return open(rules_path, 'w+').write(pickle.dumps(self.rules))

  def split_multiline_rules(self, rules):
    new_rules = []
    for rule in rules.split("\n"):
      new_rules.append(rule.lstrip().replace(';', ''))
    return new_rules

  def _is_rule(self, rule):
    for _r in self.current_rules:
      if rule in _r:
        return True
    return False

  def _execute_rule(self, rule):
    log("<<< Expecting to execute rule: '%s'" % rule)
    self.current_rules[rule.replace('iptables ', '')] = True
    return (None if debug else subprocess.Popen(
      rule.split(' '), 
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE
    ), log(rule))

  def _check_rule_state(self, rule):
    if '-D' in rule:
      current_rule = rule.replace('-D', '-A').replace('iptables ', '')
      if current_rule in self.current_rules:
        del self.current_rules[current_rule]

  def update_firewall(self, server_rules):
    rules = []

    """
    Should we block all inbound port connections as the base rule or explictly allow?
    """
    try:
      if 'block_all' not in server_rules:
        raise Exception('Not modifying block rules')

      if (server_rules['block_all'] == True \
            or self.restarted == True) \
            and '-P INPUT DROP' not in self.current_rules:
        log('Blocking all incoming connections.')
        rules = rules + self.split_multiline_rules(ipt.block_all())

      elif (server_rules['block_all'] == False \
            or self.restarted == True) \
            and '-P INPUT ACCEPT' not in self.current_rules:
        log('Allowing all incoming connections.')
        rules = rules + self.split_multiline_rules(ipt.allow_all())

    except KeyError:
      pass
    except Exception, e:
      log(e)

    """
    Look at all the port rules
    """
    for key, rule in self.rules['ports'].iteritems():
      # port rules require a strict structure, ensure this ...
      if len(rule) < 4:
        self.rules['ports'][key] = rule + (True,)
        rule = rule + (True,)
      apply_rule = rule[3]

      # no restriction on this port, anyone can connect.
      if rule[1] == 'all':
        if apply_rule:
          _rule = ipt.all_new(rule[0], rule[2])
        else:
          _rule = ipt.all_remove(rule[0], rule[2])
        rules.append(_rule)
        self._check_rule_state(_rule)

      # restrict port to all servers in the allowed list
      elif rule[1] == 'allowed':
        for ip in self.rules['allowed_ips']:
          _rule = getattr(ipt, 'ip_new' if self.rules['allowed_ips'][ip] == True \
                          and apply_rule else 'ip_remove')(ip, rule[0], rule[2])
          rules.append(_rule)
          self._check_rule_state(_rule)

      # restrict port to certain servers
      elif type(rule[1]) == list:
        for host in rule[1]:
          for ip in api.get_servers(host):
            _rule = getattr(ipt, 'ip_new' if apply_rule else 'ip_remove')(ip, rule[0], rule[2])
            rules.append(_rule)
            self._check_rule_state(_rule)

      # block everything on this port if block_all is false and we only want those on the allow list to access it
      if 'block_all' in server_rules and not rule[1] == 'all' and server_rules['block_all'] == False:
        rules.append(ipt.block_all_on_port(rule[0]))


    """
    Internal network must be able to access outside world
    """
    if '-A OUTPUT -o lo -j ACCEPT' not in self.current_rules:
      rules = rules + self.split_multiline_rules(ipt.loopback_safe())

    """
    Look at all currently applied rules and make sure we aren't reapplying them
    """
    log('Checking for duplicates ...')
    final_rules = []
    for rule in rules:
      if not self._is_rule(rule.replace('iptables ', '')):
        final_rules.append(rule)
      else:
        log('<<< Rule already exists in chain: %s' % rule)

    if len(final_rules) == 0:
      log('No new rules to add.')
      return []

    """
    Apply all the rules if not in debug mode, otherwise output them
    """
    log('Applying rules:')
    return [self._execute_rule(rule) for rule in final_rules if not rule == None]


def main(argv):
  global debug, api

  """
  Parse passed arguments.
  """
  for arg in argv:
    """
    Test mode will only output iptable commands. No commands will be run.
    https://github.com/dparlevliet/elastic-firewall/issues/9
    """
    if arg.lower() == '--test-mode':
      debug = True

  log('-----------------------------------------------------------------------')
  log("Locking the process.")
  pid = open(pid_path, 'w+')
  try:
    fcntl.lockf(pid, fcntl.LOCK_EX | fcntl.LOCK_NB)
  except IOError:
    log("Elastic firewall is already running an update.")
    return 1

  rules = ElasticRules()

  """
  Network must be able to establish connections. Ensure this is always on.
  """
  if '-P INPUT DROP' in rules.current_rules and \
      ('-A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT' not in rules.current_rules and
        '-A INPUT -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT' not in rules.current_rules):
    rules._execute_rule('iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT')

  log('Loading any previous rules.')
  rules.load()

  """
  Check server uptime to see if it's been restarted since last check
  """
  with open('/proc/uptime', 'r') as f:
    uptime_seconds = float(f.readline().split()[0])
    uptime_seconds = 0
    if uptime_seconds < rules.rules['uptime']:
      rules.restarted = True
    rules.rules['uptime'] = uptime_seconds

  """
  Parse the config
  """
  log('Loading config.')
  try:
    config = json.loads(open('%s/config.json'%app_path).read())
  except:
    log("Cannot load config file. Possible syntax error.")
    return 1

  """
  API lookup
  """
  # I hate exec. Keep an eye out for better solutions to this
  exec "from api.%s import Api" % config['server_group']

  log('Grabbing servers from the API.')
  try:
    api = Api()
    for key in config[config['server_group']]:
      setattr(api, key, config[config['server_group']][key])
    api.grab_servers()
  except Exception, e:
    log('Error: %s' % e)
    return 1

  """
  Define
  """
  found_ips       = []
  hostname        = socket.gethostname()
  server_rules    = None

  log('Trying to find the config for this server.')
  for c_hostname in config['hostnames']:
    if not re.match(c_hostname, hostname):
      continue

    log('Config found at: %s' % c_hostname)
    server_rules = config['hostnames'][c_hostname]

    if 'allow' in server_rules:
      for server in server_rules['allow']:
        for ip in api.get_servers(server):
          rules.add_allowed_ip(ip)
          found_ips.append(ip)

    """
    Add any defined safe IPs
    """
    for ip in server_rules['safe_ips']:
      rules.add_allowed_ip(ip)
      found_ips.append(ip)

    """
    Remove any old port rules
    """
    if 'firewall' in server_rules:
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
    
      """
      Assign all current/new port rules
      """
      for port_rule in server_rules['firewall']:
        log("Adding port rule %s:%s:%s" % tuple(port_rule))
        rules.add_port_rule(*port_rule) 

    """
    Remove any ips that are no longer part of the network
    """
    for ip in copy(rules.rules['allowed_ips']):
      if ip not in found_ips:
        rules.remove_allowed_ip(ip)

    """
    This server is acting as a ping server too, we must open the port.
    https://github.com/dparlevliet/elastic-firewall/issues/1
    """
    if 'server' in server_rules and server_rules['server'] == True:
      rules.add_port_rule(server_rules['server_port'], 'all', 'tcp')

    """
    Parse the rules and execute the commands
    """
    rules.update_firewall(server_rules)

  """
  This server isn't in the config
  """
  if not server_rules:
    log('Could not find a config file for this server')
    return 0

  """
  Save the current rules for comparison later
  """
  if not debug:
    rules.save() 

  os.unlink(pid_path)
  log('Complete.')
  log("-----------------------------------------------------------------------\n")
  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv))
