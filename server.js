/*
@fileoverview Elastic Firewall Server
@author David Parlevliet
@version 20130305
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
var fs = require('fs');
var e             = new Encryption();
var DEBUG         = true;

var log = function(message) {
  if (DEBUG)
    if (arguments.length==1)
      console.log('['+moment().format('D-MMMM-YY h:mm:ss')+'] '+ message);
    else
      console.log('['+moment().format('D-MMMM-YY h:mm:ss')+']', arguments);
};

var Server = function() {
  this.start    = function() {
    DEBUG = config.debug;
    this.server = net.createServer(function (socket) {
      log('Connection received');
      for (key in config.hostnames) {
        if (key == hostname.replace("\n", '') && config.hostnames[key].server == false) {
          log('This server is not accepting connections. Closing request.');
          socket.destroy();
        }
      }
      socket.on('end', function() {
        log('Connection ended');
      }).on('data', function (data) {
        try {
          var json = JSON.parse(e.decrypt(data.toString("utf8"), config.bsalt));
          if (json.api_key != config.api_key) {
            log('Incorrect API key received. Possible hack attempt.', json, data);
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
    }).listen(config.server_port, function() {
      log('Server bound');
    });
  }
}
var server = new Server();

var hostname = fs.readFileSync('/etc/hostname', 'utf8');
var config = fs.readFileSync('./config.json', 'utf8');
try {
  config = JSON.parse(config);
  server.start();
} catch (e) {
  log(e);
}