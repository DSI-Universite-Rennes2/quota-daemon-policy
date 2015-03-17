#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Cyrus Quota Check
# Version: 0.1
# Author: Sylvain Costard - Université Rennes 2
# URL : https://github.com/bb2k/cyrquota-policy 

#   This is a translation in python of Postfix quota integration perl script written by Omni Flux (http://www.omniflux.com/devel/)
#   It tries to return to overquota status of a cyrus box as fast as possible. That's why i intégrated a cache system in the code.

#   Copyright (C) 2015 Sylvain Costard
#   Université Rennes 2

#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.


import socket,sys
import netstring
import subprocess
import syslog
from daemon import runner
from werkzeug.contrib.cache import SimpleCache

# Site specific details
#
mydomains = {'xxx.fr','yyy.fr'};
aliasFile = '/etc/aliases';

#
# Responses to postfix
#
default_response   = 'DUNNO';
overquota_response = '550 5.2.2 Over quota';

# Socket config
socketFile = "/var/run/cyrus/socket/smmap";

# Input
ip   = '0.0.0.0'
port = 1143


####
##
## Functions
##
####

# return account from alias
def getAccount(mail):
  result = accountCache.get(mail)
  if result is None:
    try: 
      line = subprocess.check_output(['grep', "^"+mail+":", aliasFile])
      account = line.split(": ")  
      result = account[1].rstrip()
      accountCache.set(mail, result, timeout=5 * 60)
    except:
      return mail
  return result

# return domain of an email
def domain(mail):
  if mail.find("@") > 0 :
    (alias,domain) = mail.split("@")
    return domain
  else :
    return mail

# retrun alias part of email
def alias(mail):
  if mail.find("@") > 0 :
    (alias,domain) = mail.split("@")
    return alias
  else :
    return mail

####
##
## Main App
##
####

class App():
    def __init__(self):
      self.stdin_path = '/dev/null'
      self.stdout_path = '/dev/tty'
      self.stderr_path = '/dev/tty'
      self.pidfile_path =  '/tmp/foo.pid'
      self.pidfile_timeout = 5


    def run(self):
      try :
        self.inputSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.inputSocket.bind((ip,port))
        self.inputSocket.listen(1)
      except socket.error:
        sys.exit('Failed to create socket')

      while True:
        chaine=''
        client, adresse = self.inputSocket.accept()
        chaine=client.recv(4096)

	for line in chaine.split('\n'):
            if line.find("=") > 0 :
              (command,value) = line.split("=",1)
              attr[command] = value
            else :
              syslog.syslog("Ignoring Garbage : " + line)

        if 'request' in attr and attr['request'] != 'smtpd_access_policy':
          syslog.syslog("Error : Bad Request : " + command)
          sys.exit("Bad request")

        quotaResult = "action="+default_response

        if 'recipient' in attr:
          recipient = getAccount(alias(attr['recipient']))

          if domain(attr['recipient']).lower() in mydomains:
            quotaResult = quotaCache.get(alias(recipient))
            cached      = " (from cache)"

            if quotaResult is None:
              cached = " "
              s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
              s.connect(socketFile)
              s.send(netstring.encode("0 " + alias(recipient)))
              data = s.recv(1024)
              s.close()
              if not data:
                syslog.syslog("No data received")
                sys.exit("No data received")

              for packet in decoder.feed(data):
                if packet.find("Over quota") >= 0 :
                  quotaResult = "action="+overquota_response
                else :
                  quotaResult = "action="+default_response
                quotaCache.set(value, quotaResult, timeout=5 * 60)
          else :
             syslog.syslog ("Skipping external domain: " + domain(recipient).lower())

          #syslog.syslog ("cyrquota-policy response: "+ recipient + " " + quotaResult + cached)
          client.send(quotaResult + '\n\n')
          client.close()

####
## 
## Main process
##
#####
attr={}
cached =  ""
# netstring decoder
decoder = netstring.Decoder()

# cache initialization
accountCache = SimpleCache()
quotaCache   = SimpleCache()

# syslog init
syslog.openlog(logoption=syslog.LOG_PID, facility=syslog.LOG_MAIL)


app = App()
daemon_runner = runner.DaemonRunner(app)
daemon_runner.do_action()



