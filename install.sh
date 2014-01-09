#!/bin/bash
ln -f -s /usr/local/share/elastic-firewall/elastic-firewall.sh /etc/init.d/elastic-firewall
chmod +x /etc/init.d/elastic-firewall
update-rc.d elastic-firewall defaults
cp /usr/local/share/elastic-firewall/config-sample.json /usr/local/share/elastic-firewall/config.json
mkdir -p /var/log/elastic-firewall