# DOCKER-VERSION 0.3.4
#
# Example:
# docker build -t firewall .
# docker run -v "/usr/local/share/elastic-firewall/:/usr/local/share/elastic-firewall/" -i -t firewall /bin/bash
#
FROM    ubuntu:12.10
RUN     apt-get update
RUN     apt-get install -y --force-yes nano iptables software-properties-common python-software-properties git python-crypto
RUN     yes w | add-apt-repository ppa:richarvey/nodejs
RUN     apt-get update
RUN	apt-get install -y --force-yes nodejs npm
RUN     yes w | npm install -g forever moment
CMD	/usr/local/share/elastic-firewall/install.sh
