#! /usr/bin/python
import sys
import os
import json
import socket
import ext.iptables as ipt


class ElasticRules():
  rules = {
    'allowed_ips': {},
    'ports': {},
  }

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
      self.rules = json.loads(open('./rules.json').read())
    except:
      pass

  def save(self):
    for ip, allowed in self.rules['allowed_ips'].iteritems():
      if not allowed:
        del self.rules['allowed_ips'][ip]
    return open('./rules.json', 'w').write(json.dumps(self.rules, separators=(',', ':')))

  def update_firewall(self):
    for key, rule in self.rules['ports'].iteritems():
      if rule[1] == 'all':
        ipt.all_new(rule[0], rule[2])
      else:
        for ip in self.rules['allowed_ips']:
          ipt.ip_new(ip, rule[0], rule[2])


def main():
  rules = ElasticRules()
  rules.load()
  config = json.loads(open('./config.json').read())

  # I hate exec. Keep an eye out for better solutions to this
  exec "from api.%s import Api" % config['server_group']

  api = Api()
  for key in config[config['server_group']]:
    setattr(api, key, config[config['server_group']][key])
  api.grab_servers()

  found_ips = []
  hostname  = socket.gethostname()
  if hostname in config['hostnames']:
    for server in config['hostnames'][hostname]['allow']:
      for ip in api.get_servers(server):
        rules.add_allowed_ip(ip)
        found_ips.append(ip)

  for ip in config['hostnames'][hostname]['safe_ips']:
    rules.add_allowed_ip(ip)
    found_ips.append(ip)

  for port_rule in config['hostnames'][hostname]['firewall']:
    rules.add_port_rule(*port_rule)

  for ip in found_ips:
    if ip not in rules.rules['allowed_ips']:
      rules.remove_allowed_ip(ip)

  rules.update_firewall()
  rules.save()


if __name__ == '__main__':
  sys.exit(main())