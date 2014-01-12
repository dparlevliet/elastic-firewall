"""
@fileoverview Digital Ocean API
@author David Parlevliet
@version 20130315
@preserve Copyright 2013 David Parlevliet.

Digital Ocean API
=================
Class to get the server details via the Digital Ocean API.
"""
import requests
import json
import re

class Api():
  group_name  = "Digital Ocean"
  client_key  = None
  api_key     = None
  servers     = {}

  def __init__(self, **kwargs):
    for key in kwargs:
      setattr(self, key, kwargs[key])

  def grab_servers(self):
    DROPLETS_URL  = 'https%s/droplets/?client_id=%s&api_key=%s' % \
                      ('://api.digitalocean.com',
                        self.client_key,
                        self.api_key)

    try:
      droplets = requests.get(DROPLETS_URL)
    except:
      raise Exception("Fatal error: Unable to connect to API")

    try:
      data        = json.loads(droplets.text)
    except:
      raise Exception("Fatal error: No droplets found")

    for droplet in data['droplets']:
      name = droplet['name']
      if name not in self.servers:
        self.servers[name] = []
      self.servers[name].append(droplet['ip_address'])

  def get_servers(self, name):
    servers = []
    for c_hostname in self.servers:
      servers = servers + (self.servers[c_hostname] if re.match(name, c_hostname) else [])
    return servers

