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


if SSL:
    irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    secure = ssl.wrap_socket(irc,
            ca_certs='/etc/ssl/cert.pem',
            cert_reqs=ssl.CERT_REQUIRED)
    secure.connect((server, port))

    secure.write('NICK {}\r\n'.format(nickname))
    secure.write('USER {} {} {} :{}\r\n'.format(nickname, hostname, server, realname))

else:
    irc = socket.socket()
    irc.connect((server, port))

    irc.send('NICK {}\r\n'.format(nickname))
    irc.send('USER {} {} {} :{}\r\n'.format(nickname, hostname, server, realname))


for channel in channels:
    if SSL:
        secure.write('JOIN {}\r\n'.format(channel))
    else:
        irc.send('JOIN {}\r\n'.format(channel))


while True:
    try:
        if SSL:
            stream = secure.read()
        else:
            stream = irc.recv(2048)

        ## logging function
        def logger(channel, log_message):
            logfile = HOME + '/.blue/' + channel + '.log'
            with open(logfile, 'a') as fh_:
                fh_.write(log_message)

        ## capture messages; send to logger
        if re.match(r'^:(.*)!~?.*@.*\sPRIVMSG\s(#[\w-]+[^:])\s(:.*)$', stream):
            component = re.match(r'^:(.*)!~?.*@.*\sPRIVMSG\s(#[\w-]+[^:])\s(:.*)$', stream)
            timestamp = datetime.now().strftime('%Y-%m-%d %X')
            sender = component.groups(1)[0].strip()
            channel = component.groups(1)[1].strip()
            message = component.groups(1)[2].strip()[1:]
            log_message = '{} {} {}: {}\n'.format(timestamp, channel, sender, message)
            logger(channel, log_message)

        ## capture join messages; send to logger
        if re.match(r'^:(.*)!(~?.*@.*)\sJOIN\s(#[\w-]+)', stream):
            component = re.match(r'^:(.*)!(~?.*@.*)\sJOIN\s(#[\w-]+)', stream)
            timestamp = datetime.now().strftime('%Y-%m-%d %X')
            sender = component.groups(1)[0].strip()
            useraddr = component.groups(1)[1].strip()
            channel = component.groups(1)[2].strip()
            log_message = '{} {} {} ({}) has joined {}\n'.format(timestamp, channel, sender, useraddr, channel)
            logger(channel, log_message)

        ## keepalive ping/pong
        if re.match(r'^PING (.*)$', stream):
            keepalive = re.match(r'^PING (.*)$', stream)
            keepalive = keepalive.groups(1)[0]
            if SSL:
                secure.write('PONG :{}\r\n'.format(keepalive))
            else:
                irc.send('PONG :{}\r\n'.format(keepalive))

    except IOError:
        print "Unable to open {}".format(logfile)
        sys.exit()

    except KeyboardInterrupt:
        print "Exiting on CTRL-C\n"
        if SSL:
            secure.write('QUIT\r\n')
            secure.close()
        else:
            irc.send('QUIT\r\n')
            irc.close()
        sys.exit()
