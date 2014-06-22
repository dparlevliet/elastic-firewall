#!/bin/sh

EF_LOGPATH=/var/log/elastic-firewall
EF_LOG=$EF_LOGPATH/run.log
EF_PATH=/usr/local/share/elastic-firewall
EF_PID=/var/run/elastic-firewall.pid

case "$1" in
start)

  if [ ! -d "$EF_LOGPATH" ]; then
    mkdir $EF_LOGPATH
  fi
  forever start -a -l $EF_LOG --pidFile $EF_PID --sourceDir $EF_PATH -w server.js
  python $EF_PATH/pinger.py
  python $EF_PATH/update_firewall.py

;;

stop)

  forever stop --sourceDir $EF_PATH -w server.js
  python $EF_PATH/pinger.py

;;

restart)
  $0 stop
  $0 start
;;

*)
  echo "Usage: $0 {start|stop|restart}"
  exit 1
esac
