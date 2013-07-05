"""
@fileoverview Digital Ocean API
@author David Parlevliet
@version 20130315
@preserve Copyright 2013 David Parlevliet.

Digital Ocean API
=================
Class to get the server details via the Digital Ocean API.
"""
import urllib2
import json

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
      droplets      = urllib2.urlopen(DROPLETS_URL)
    except urllib2.URLError:
      raise Exception("Fatal error: Unable to connect to API")

    try:
      data        = json.loads(droplets.read())
    except:
      raise Exception("Fatal error: No droplets found")

    for droplet in data['droplets']:
      if droplet['status'] == 'active':
        name = droplet['name']
        if name not in self.servers:
          self.servers[name] = []
        self.servers[name].append(droplet['ip_address'])

  def get_servers(self, name):
    return self.servers[name] if name in self.servers else None

