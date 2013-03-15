
var net           = require('net');
var moment        = require('moment');
var Encryption    = require('./ext/encryption.js');
var e             = new Encryption();
var DEBUG         = false;

var log = function(message) {
  if (DEBUG)
    if (arguments.length>1)
      console.log('['+moment().format('D-MMMM-YY h:mm:ss')+'] '+ message);
    else
      console.log('['+moment().format('D-MMMM-YY h:mm:ss')+']', arguments);
};

var Server = function() {
  this.start    = function() {
    fs = require('fs')
    var config = fs.readFileSync('./config.json', 'utf8');
    config = JSON.parse(config);
    DEBUG = config.debug;
    this.server = net.createServer(function (socket) {
      log('Connection received');
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
              // todo: update firewall
              console.log('Updating firewall');
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
server.start();