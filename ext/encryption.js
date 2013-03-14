/*
@fileoverview Node.JS Blowfish encryption.
@author David Parlevliet
@version 20130305
@preserve Copyright 2013 David Parlevliet.

Encryption
==========
Blowfish encryption. Tested Decypherable between PHP<->Node.JS<->Python
*/
var crypto = require('crypto');
var algorithm = "bf-ecb";

function pad(text) {
  var pad_bytes = 8 - (text.length % 8)
  for (var x=1; x<=pad_bytes;x++)
    text = text + String.fromCharCode(0)
  return text;
}

function Encryption() {
  self = this;
  self.encrypt = function(data, key) {
    var cipher = crypto.createCipheriv(algorithm, Buffer(key), '');
    cipher.setAutoPadding(false);
    try {
      return Buffer(cipher.update(pad(data),
                      'utf8', 'binary') + cipher.final('binary'), 'binary')
                        .toString('hex');
    } catch (e) {
      console.log('Encryption error: ', e, data, key);
      return null;
    }
  }

  self.decrypt = function(data, key) {
    var decipher = crypto.createDecipheriv(algorithm, Buffer(key), '');
    decipher.setAutoPadding(false);
    try {
      return (decipher.update(Buffer(data, 'hex').toString('binary'),
              'binary', 'utf8') + decipher.final('utf8')).replace(/\x00+$/g, '');
    } catch (e) {
      console.log('Decryption error: ', e, data, key);
      return null;
    }
  }
}

module.exports = Encryption;