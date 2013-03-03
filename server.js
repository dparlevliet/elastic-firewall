
var net           = require('net');
var moment        = require('moment');

var log = function(message) {
  if (DEBUG)
    console.log('['+moment().format('M-D-YY h:mm:ss')+'] '+message);
};

var Server = function() {
  this.api_key  = API_KEY;
  this.port     = SERVER_PORT;
  this.start    = function() {
    this.server = net.createServer(function (socket) {
      log('Connection received');
      socket.on('end', function() {
        log('Connection ended');
      });
      socket.on('data', function (data) {
        try {
          var json = JSON.parse(data.toString('utf8'));
          if (json.api_key != this.api_key) {
            log('Incorrect API key received. Possible hack attempt.', json, data);
          }
        } catch (e) {
          log('Unsupported message received: ', data.toString('utf8'));
        }
      });
    }).listen(this.port, function() {
      log('Server bound');
    });
  }
}
var server = new Server();