Elastic Firewall
================

An unobtrusive, non-assuming elastic service for your cloud cluster. Currently
it is designed to only listen for a ping message from your servers when they
come online or go offline and update the firewall rules accordingly.


Visual Overview
===============
<img src="http://c2journal.com/wp-content/uploads/2013/07/elastic_firewall-1.jpg">


How it works
============
Install this package on each of your cloud servers. If <tt>server</tt> is defined
as true for any server in your config file, then the nodejs ping receiver will
be launched at boot-time and start listening for requests.

When a message is received, it will decrypt the message and verify it. If it is
confirmed to be a new ping message then the <tt>update_firewall.py</tt> script
is run, which will download all your cluster information via the specified API
rules, it will then compare those results against previous results and make
iptable adjustments to your iptables accordingly.


Dependencies
============

  * Node.JS (v0.8+)
  * Python 2.7 (untested with Python 3)
  * Node.JS forever


Ubuntu Dependency Installation
==============================
```
apt-get update; \
apt-get install -y --force-yes software-properties-common python2.7-dev python-software-properties git python-pip python-crypto; \
yes w | add-apt-repository ppa:richarvey/nodejs; \
apt-get update; \
apt-get install -y --force-yes nodejs npm; \
yes w | pip install netifaces requests; \
yes w | npm install -g forever moment;
```


Installation & Configuration
============================
```
cd /usr/local/share/;
git clone git://github.com/dparlevliet/elastic-firewall.git; \
ln -f -s /usr/local/share/elastic-firewall/elastic-firewall.sh /etc/init.d/elastic-firewall; \
chmod +x /etc/init.d/elastic-firewall; \
update-rc.d elastic-firewall defaults; \
cp /usr/local/share/elastic-firewall/config-sample.json /usr/local/share/elastic-firewall/config.json;
```


Example config
==============
The config for this application is stored using JSON. If you have trouble coming
up with secure api_keys or salts, then use <a href="http://passwdtools.com">http://passwdtools.com</a>.
Also, note that the salt for Blowfish cannot exceed 448 bits, so keep your bsalt
below or equal to 56 characters.
```
{
  "server_group": "standalone",
  "digital_ocean": {},
  "hostnames": {
    "elastic-firewall": {
      "api_key": "=MGuNrNGg6dEap1lle#w;eC1QEwC_ncJV^aOYLA56-,,:oBH5)PF))",
      "bsalt": ":2hk)BKAq 1,4F3L",
      "block_all": true,
      "server_port": 23565,
      "server": true,
      "ping": [
        "dave-*"
      ],
      "allow": [
        "web"
      ],
      "firewall": [
        ["22", "all", "tcp"],
        ["80", "allowed", "tcp"],
        ["21:23", "allowed", "tcp"],
        [
          "8080",
          [
            "balancer-*",
            "cache-1"
          ],
          "tcp"
        ]
      ],
      "safe_ips": [
        "192.0.188.111"
      ]
    },
    "dave-*": {
      "api_key": "=MGuNrNGg6dEap1lle#w;eC1QEwC_ncJV^aOYLA56-,,:oBH5)PF))",
      "bsalt": ":2hk)BKAq 1,4F3L",
      "block_all": true,
      "server_port": 23565,
      "server": false,
      "ping": [
        "elastic-firewall"
      ],
      "allow": [
        "mysql-*"
      ],
      "firewall": [],
      "safe_ips": []
    }
  }
}
```


Digital Ocean API usage
=======================
```
{
  "server_group": "digital_ocean",
  "digital_ocean": {
    "client_key": "abcd",
    "api_key": "abcde"
  },
  ... the rest of your server settings here ...
}
```


Config explained
================
```
  # name of the api file (without .py) located in the api/ folder
  "server_group": "digital_ocean",

  # specific information only used by the Digital Ocean API file.
  "digital_ocean": {
    "client_key": "abcd",
    "api_key": "abcde"
  },

  "hostnames": {
    # servers host name
    "elastic-firewall": {

      # block all incoming connection attempts as a general rule
      "block_all": true,

      # API key to verify the messages received by the server are from within your
      # cluster.
      "api_key": "=MGuNrNvGg6dEap1lle#w;eC1QEwC_ncJV^aOYLA56-,,:oBH5)PF))",

      # salt for the message encryption. must be <= 448 bits
      "bsalt": ":2hk)BKAq 1,4F3L",

      # port for the server(s) to run on
      "server_port": 23565,

      # Is this server going to act as a ping receiver?
      "server": true,

      # which servers to ping (by hostname)
      "ping": [
        # regex support for hostname list in ping list
        "dave-*"
      ],

      # which servers to grant access to?
      "allow": [
        # any server with the hostname 'web'
        "web"
      ],

      # firewall rules
      "firewall": [
        # [ port, whom, protocol ]
        # whom = [all | allowed]

        # all means any IP
        ["22", "all", "tcp"],

        # allowed means only those in the allow list plus the safe_ips list
        ["80", "allowed", "tcp"],

        # port-range support
        ["21:23", "allowed", "tcp"],

        # list of hostnames that are allowed access to this port
        [
          "8080",
          [
            # regex support for hostnames
            "balancer-*",
            "cache-1"
          ],
          "tcp"
        ]

        # Because this host is defined as a server ("server": true), one extra rule
        # will be added automatically. 
        # Note: You do not need to do this, it will be done for you!
        # ["23565", "all", "tcp"]
      ],

      "safe_ips": [
        # specific IPs to allow access to (ie. you or your team)
        "192.0.188.111"
      ]
    },
    # regex support for hostnames
    "dave-*": {
      "api_key": "=MGuNrNGg6dEap1lle#w;eC1QEwC_ncJV^aOYLA56-,,:oBH5)PF))",
      "bsalt": ":2hk)BKAq 1,4F3L",
      "block_all": true,
      "server_port": 23565,
      "server": false,
      "ping": [
        "elastic-firewall"
      ],
      "allow": [
        # regex support for hostname list in allow list
        "mysql-*"
      ],
      "firewall": [],
      "safe_ips": []
    }
  }
```


update_firewall.py arguments
============================
```
--test-mode       Enables debug mode. iptables commands will run without being applied.
```


Log file
========
```
tail -f /var/log/elastic-firewall/firewall.log
```


Testing with Docker
===================
```
docker build -t firewall .
docker run -v "/usr/local/share/elastic-firewall/:/usr/local/share/elastic-firewall/" -i -t firewall /bin/bash
cd /usr/local/share/elastic-firewall/;
nano config.json;
python update_firewall.sh --test-mode
```


Testing with Vagrant
====================
```
vagrant up
vagrant ssh
cd /usr/local/share/elastic-firewall/;
nano config.json;
python update_firewall.sh --test-mode
```


Notes
=====
You do not need to restart the service if you make changes to the config file, 
it will restart its self.


License
=======
Copyright (c) 2012 David Parlevliet

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

