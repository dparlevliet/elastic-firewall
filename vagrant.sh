#/bin/bash
echo "********************************************************************************"
echo "*                                                                              *"
echo "*            This application will now be installed and configured             *"
echo "*            =====================================================             *"
echo "*                                                                              *"
echo "*           This may take a few minutes. Go get a coffee and I'll let          *"
echo "*           you know when I'm done.                                            *"
echo "*                                                                              *"
echo "********************************************************************************"

apt-get update; \
apt-get install -y --force-yes software-properties-common python2.7-dev python-software-properties git python-pip python-crypto; \
yes w | add-apt-repository ppa:richarvey/nodejs; \
apt-get update; \
apt-get install -y --force-yes nodejs npm; \
yes w | pip install netifaces requests; \
yes w | npm install -g forever moment;

echo "*********Complete!**************************************************************"
exit 0