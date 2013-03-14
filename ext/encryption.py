"""
@fileoverview Python Blowfish encryption.
@author David Parlevliet
@version 20130305
@preserve Copyright 2013 David Parlevliet.

Encryption
==========
Blowfish encryption. Tested Decypherable between PHP<->Node.JS<->Python
"""
from Crypto.Cipher import Blowfish
from base64 import b64encode, b64decode
from django.conf import settings
from random import randrange
from binascii import unhexlify, hexlify


def Encrypt(text, key):
  pad_bytes = 8 - (len(text) % 8)
  for i in range(pad_bytes):
    text += chr(0)
  cipher = Blowfish.new(key, Blowfish.MODE_ECB, '')
  return str(cipher.encrypt(text)).encode("hex")


def Decrypt(text, key):
  try:
    cipher = Blowfish.new(key, Blowfish.MODE_ECB, '')
    output = cipher.decrypt(text.decode("hex"))
    # Trim off extra nulls
    while output[-1] == chr(0):
      output = output[:-1]
    return output
  except:
    return None
