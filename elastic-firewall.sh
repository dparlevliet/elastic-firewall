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

;;

stop)

  forever stop --sourceDir $EF_PATH -w server.js

;;

restart)
  $0 stop
  $0 start
;;

*)
  echo "Usage: $0 {start|stop|restart}"
  exit 1
esac