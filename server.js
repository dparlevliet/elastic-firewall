/*
@fileoverview Elastic Firewall Server
@author David Parlevliet
@version 20140111
@preserve Copyright 2013 David Parlevliet.

Elastic Firewall Server
=======================
Server for receiving Elastic Firewall ping messages & running the update_firewall
script.
*/
var sys           = require('sys');
var exec          = require('child_process').exec;
var net           = require('net');
var moment        = require('moment');
var Encryption    = require('./ext/encryption.js');
var fs            = require('fs');
var e             = new Encryption();
var server_config = {};
var hostname      = fs.readFileSync('/etc/hostname', 'utf8');
hostname          = hostname.replace("\n", '');
var config        = fs.readFileSync(__dirname+'/config.json', 'utf8');
var cron          = null;
var log_file      = '/var/log/elastic-firewall/server.log';

var log = function(message) {
  if (arguments.length==1) {
    message = '['+moment().format('D-MMMM-YY h:mm:ss')+'] '+ message;
    console.log(message);
    fs.appendFile(log_file, message, function (err) {
      console.log(err);
    });
  } else {
    console.log('['+moment().format('D-MMMM-YY h:mm:ss')+']', arguments);
  }
};

var Server = function() {
  this.start = function() {

    log("I'm online! Pinging everyone.");
    exec("python "+__dirname+"/pinger.py", function(error, stdout, stderr) {
      sys.puts(stdout);
    });

    if (typeof(server_config.cron) != 'undefined' && parseInt(server.cron) > 0) {
      log('Starting cron job ...');
      clearInterval(cron);
      cron = setInterval(function() {
        log('Cron: Updating firewall.');
        exec("python "+__dirname+"/update_firewall.py", function(error, stdout, stderr) {
          if (stdout) log(stdout);
          if (stderr) log(stderr);
        });
      }, parseInt(server_config.cron));
    }

    // Make sure the user hasn't ballsed up the config file.
    if (typeof(server_config.server_port) == 'undefined') {
      log('Not starting server because "server_port" is undefined.');
      return;
    }

    if (parseInt(server.server_port) < 0 || parseInt(server.server_port) > 65535) {
      log('There was an error processing your port number. Port numbers must be between 1-65535.');
      return;
    }

    // Create the socket to receive online notifications
    this.server = net.createServer(function (socket) {
      log('Connection received');
      if (!server_config.server) {
        log('This server is not accepting connections. Closing request.');
        socket.destroy();
      }
      socket.on('end', function() {
        log('Connection ended');
      }).on('data', function (data) {
        try {
          var json = JSON.parse(e.decrypt(data.toString("utf8"), server_config.bsalt));
          if (json.api_key != server_config.api_key) {
            log('Incorrect API key received. Possible hack attempt.', json, data);
            return;
          }
          log('Message received:')
          switch (json.area) {
            case 'ping':
              console.log('Updating firewall');
              exec("python "+__dirname+"/update_firewall.py", function(error, stdout, stderr) {
                sys.puts(stdout)
              });
              break;
          }
        } catch (e) {
          log('Unsupported message received: ', data.toString('utf8'));
        }
      });
    }).listen(server_config.server_port, function() {
      log('Server bound');
    });
    //
  }
}
var server = new Server();

try {
  config = JSON.parse(config);
  for (key in config.hostnames) {
    var re = new RegExp(key);
    if (key == hostname || re.exec(hostname)) {
      for (var attr in config.hostnames[key]) {
        server_config[attr] = config.hostnames[key][attr];
      }
    }
  }
  server.start();
} catch (e) {
  log(e);
}
