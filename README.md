Elastic Firewall
================

An unobtrusive, non-assuming elastic service for your cloud cluster. Currently
it is designed to only listen for a ping message from your servers when they
come online or go offline and update the firewall rules accordingly. But, it
could technically do a lot more than that if the need arises.

If the needs for this project expand, the name will be adjusted to something more
generic.


Dependencies
============

  * Node.JS (v0.8+)
  * Python 2.7 (untested with Python 3)
  * Node.JS forever


Ubuntu Installation
===================
```
apt-get install software-properties-common python-software-properties
add-apt-repository ppa:richarvey/nodejs
apt-get update
apt-get install nodejs npm
```


Installation & Configuration
============================
```
ln -f -s /usr/local/share/elastic-firewall/elastic-firewall.sh /etc/init.d/elastic-firewall
chmod +x /etc/init.d/elastic-firewall
update-rc.d elastic-firewall defaults
```


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

