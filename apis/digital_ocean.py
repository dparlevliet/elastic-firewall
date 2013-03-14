class Api():
  group_name  = "Digital Ocean"
  client_key  = None
  api_key     = None
  servers     = None

  def __init__(self, **kwargs):
    for key in kwargs:
      setattr(self, key, kwargs[key])

  def grab_servers(self):
    DROPLETS_URL  = 'https%s/droplets/?client_id=%s&api_key=%s' % \
                      ('://api.digitalocean.com',
                        self.client_key,
                        self.api_key)

    droplets      = urllib2.urlopen(DROPLETS_URL)
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

