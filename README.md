Blue
----

IRC logging bot. Supports plaintext and SSL connections.

Requires: os, re, sys, yaml, socket, datetime

config
------

Create a ~/.blue/config.yml:

.. code-block:: yaml

    nickname: 'botname'
    hostname: hostname
    realname: 'bot real name'
    server: 'irc.freenode.net'
    port: 6667 ## 7000 for SSL
    SSL: False ## True for SSL

    channels:
      - '#channel1'
      - '#channel2'
      - '#channel3'
      - '#channel4'

connect
-------

.. code-block:: bash

    python2 blue.py

logs
----

This creates logs in ~/.blue/$channel.log.
