#!/usr/bin/env python2


import os
import re
import sys
import ssl
import yaml
import socket
from datetime import datetime


HOME = os.path.expanduser('~')

if not os.path.exists(HOME + '/.blue/config.yml'):
    print 'Missing config file: ~/.blue/config.yml'
    sys.exit()


try:
    with open(HOME + '/.blue/config.yml') as fh_:
        config = yaml.safe_load(fh_)

        nickname = config['nickname']
        hostname = config['hostname']
        realname = config['realname']
        server = config['server']
        port = config['port']
        channels = config['channels']
        SSL = config['SSL']

except IOError as io:
    print 'Failed to open config file.\n'
    print io
    sys.exit()

class blueBot:
    def __init__(self):
        self.userlist = {}

    def connect(self, server, port):
        if SSL:
            self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.ssl = ssl.wrap_socket(irc,
                    ca_certs='/etc/ssl/cert.pem',
                    cert_reqs=ssl.CERT_REQUIRED)
            self.ssl.connect((server, port))
        
        else:
            self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.irc.connect((server, port))
        
    def auth(self, nickname, hostname, server, realname):
        if SSL:
            self.ssl.write('NICK {}\r\n'.format(nickname))
            self.ssl.write('USER {} {} {} :{}\r\n'.format(nickname, hostname, server, realname))
        else:
            self.irc.send('NICK {}\r\n'.format(nickname))
            self.irc.send('USER {} {} {} :{}\r\n'.format(nickname, hostname, server, realname))

    def join(self, channels):
        for channel in channels:
            if SSL:
                self.ssl.write('JOIN {}\r\n'.format(channel))
            else:
                self.irc.send('JOIN {}\r\n'.format(channel))

    def add_user(self, channel, user):
        if not user in self.userlist[channel]:
            self.userlist[channel].append(user)
            print 'Adding {} to {}...'.format(user, channel)
        else:
            print 'User {} already in list {}'.format(user, channel)

    def del_user(self, channel, user):
        if user in self.userlist[channel]:
            self.userlist[channel].remove(user)
            print 'Removing {} from {}...'.format(user, channel)
        else:
            print 'Expected {} in {}; not found'.format(user, channel)

    def logger(self, channel, log_message):
        logfile = HOME + '/.blue/' + channel + '.log'
        with open(logfile, 'a') as fh_:
            fh_.write(log_message)

    def populate(self, channel, name_result):
        if channel in self.userlist:
            for item in name_result:
                user = item.split()
                user = user[1:]
                self.userlist[channel].extend(user)
        else:
            self.userlist[channel] = []
            self.populate(channel, name_result)

## initialize class
bot = blueBot()
bot.connect(server, port)
bot.auth(nickname, hostname, server, realname)
bot.join(channels)

while True:
    try:
        if SSL:
            stream = bot.ssl.read()
        else:
            stream = bot.irc.recv(4096)

        ## compile regex for userlist
        for channel in channels:
            name_regex = nickname + ' = ' + channel + ':?(.*)'
            name = re.compile(name_regex)
        
            name_result = name.findall(stream)
            if name_result:
                print 'Populating userlist for {}...'.format(channel)
                bot.populate(channel, name_result)

        ## capture messages; send to logger
        if re.match(r'^:(.*)!~?.*@.*\sPRIVMSG\s(#[\w-]+[^:])\s(:.*)$', stream):
            component = re.match(r'^:(.*)!~?.*@.*\sPRIVMSG\s(#[\w-]+[^:])\s(:.*)$', stream)
            timestamp = datetime.now().strftime('%Y-%m-%d %X')
            user = component.groups(1)[0].strip()
            channel = component.groups(1)[1].strip()
            message = component.groups(1)[2].strip()[1:]
            log_message = '{} {} {}: {}\n'.format(timestamp, channel, user, message)
            bot.logger(channel, log_message)

        ## capture join messages; send to logger
        if re.match(r'^:(.*)!(~?.*@.*)\sJOIN\s(#[\w-]+)', stream):
            component = re.match(r'^:(.*)!(~?.*@.*)\sJOIN\s(#[\w-]+)', stream)
            timestamp = datetime.now().strftime('%Y-%m-%d %X')
            user = component.groups(1)[0].strip()
            useraddr = component.groups(1)[1].strip()
            channel = component.groups(1)[2].strip()
            log_message = '{} {} {} ({}) has joined {}\n'.format(timestamp, channel, user, useraddr, channel)
            if nickname not in user:
                bot.add_user(channel, user)
                bot.logger(channel, log_message)

        ## capture quit messages; send to logger
        if re.match(r'^:(.*)!(~?.*@.*)\sQUIT\s(:.*)', stream):
            component = re.match(r'^:(.*)!(~?.*@.*)\sQUIT\s(:.*)', stream)
            timestamp = datetime.now().strftime('%Y-%m-%d %X')
            user = component.groups(1)[0].strip()
            useraddr = component.groups(1)[1].strip()
            message = component.groups(1)[2].strip()
            for channel in channels:
                try:
                    if user in bot.userlist[channel]:
                        group = channel
                        log_message = '{} {} {} ({}) has left {}: {}\n'.format(timestamp, group, user, useraddr, group, message)
                        bot.del_user(group, user)
                        bot.logger(group, log_message)
                except KeyError:
                    bot.userlist[channel] = []

        ## keepalive ping/pong
        if re.match(r'^PING (.*)$', stream):
            keepalive = re.match(r'^PING (.*)$', stream)
            keepalive = keepalive.groups(1)[0]
            if SSL:
                bot.ssl.write('PONG :{}\r\n'.format(keepalive))
            else:
                bot.irc.send('PONG :{}\r\n'.format(keepalive))

    except Exception as error:
        print error

    except IOError:
        print "Unable to open {}".format(logfile)
        sys.exit()

    except KeyboardInterrupt:
        print "Exiting on CTRL-C\n"
        if SSL:
            bot.ssl.write('QUIT\r\n')
            bot.ssl.close()
        else:
            bot.irc.send('QUIT\r\n')
            bot.irc.close()
        sys.exit()
