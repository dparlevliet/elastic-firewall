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
import socket
import ext.iptables as ipt
import re
import fcntl
import subprocess
import time


app_path = '/usr/local/share/elastic-firewall'
pid_path = '/var/run/elastic-firewall-update.pid'
log_path = '/var/log/elastic-firewall/firewall.log'

debug    = False
api      = None


def log(output):
  output = "[%s] %s" % (time.ctime(), output)
  if debug:
    print output
  open(log_path, 'a').write("\n%s" % output)


class ElasticRules():
  rules = {
    'allowed_ips': {},
    'ports': {},
  }

  def __init__(self):
    ipt.current_rules = ipt.rules_list()

  def add_port_rule(self, port, whom, type):
    key = "%s:%s:%s" % (port, type, whom)
    self.rules['ports'][key] = (port, whom, type)

  def remove_port_rule(self, port, whom, type):
    key = "%s:%s:%s" % (port, type, whom)
    if key not in self.rules['ports']:
      return None
    del self.rules['ports'][key]

  def add_allowed_ip(self, ip):
    self.rules['allowed_ips'][ip] = True

  def remove_allowed_ip(self, ip):
    if ip not in self.rules:
      return None
    self.rules['allowed_ips'][ip] = False

  def load(self):
    try:
      self.rules = json.loads(open('/var/log/elastic-firewall/rules.json'%app_path).read())
      self.loaded_rules = copy(self.rules)
    except:
      pass

  def save(self):
    for ip, allowed in self.rules['allowed_ips'].iteritems():
      if not allowed:
        del self.rules['allowed_ips'][ip]
    return open('/var/log/elastic-firewall/rules.json'%app_path, 'w').write(json.dumps(self.rules))

  def update_firewall(self):
    rules = []
    for key, rule in self.rules['ports'].iteritems():
      # no restriction on this port, anyone can connect.
      if rule[1] == 'all':
        rules.append(ipt.all_new(rule[0], rule[2]))

      # restrict port to all servers in the allowed list
      elif rule[1] == 'allowed':
        for ip in self.rules['allowed_ips']:
          rules.append(ipt.ip_new(ip, rule[0], rule[2]))

      # restrict port to certain servers
      elif type(rule[1]) == list:
        for host in rule[1]:
          for ip in api.get_servers(host):
            rules.append(ipt.ip_new(ip, rule[0], rule[2]))

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

  try:
    if 'block_all' in server_rules and server_rules['block_all'] == True \
                                    and 'block_all_assigned' not in rules.rules:
      log('Blocking all incoming connections.')
      ipt.block_all()
      rules.rules['block_all_assigned'] = True
      del rules.rules['allow_all_assigned']
    elif 'allow_all_assigned' not in rules.rules:
      log('Allowing all incoming connections.')
      ipt.allow_all()
      rules.rules['allow_all_assigned'] = True
      del rules.rules['block_all_assigned']
  except KeyError:
    pass

  # Add any defined safe IPs so the list of firewall rules list.
  for ip in server_rules['safe_ips']:
    rules.add_allowed_ip(ip)
    found_ips.append(ip)

  # Assign all our port rules to the firewall rules list.
  for port_rule in server_rules['firewall']:
    rules.add_port_rule(*port_rule)

  # Add all our found server ips to the firewall rules list.
  for ip in found_ips:
    if ip not in rules.rules['allowed_ips']:
      rules.remove_allowed_ip(ip)

  # This server is acting as a ping server too, we must open the port.
  # https://github.com/dparlevliet/elastic-firewall/issues/1
  if server_rules['server'] == True:
    rules.add_port_rule(server_rules['server_port'], 'all', 'tcp')

  rules.update_firewall()
  rules.save() # save the rules for comparison later
  ipt.loopback_safe() # internal network must be able to access outside world
  os.unlink(pid_path)
  log('Complete.')
  return 0


if __name__ == '__main__':
  sys.exit(main(sys.argv))
