Cyrus Daemon Quota Check
-----------------

**Version**:   0.1

**Author** :   Sylvain Costard - Université Rennes 2
  
**URL**: https://github.com/DSI-Universite-Rennes2/quota-daemon-policy


This is a translation in python of Postfix quota integration perl script written by Omni Flux (http://www.omniflux.com/devel/)
It is daemonized
It tries to return to overquota status of a cyrus box as fast as possible. That's why i integrated a cache system in the code.

**Usage** : 

quota-daemon.py start|stop|restart

**Limitation** :

This method will not catch overquota accounts if postfix
rewrites the address before performing local delivery
(aliases, virtual domains).

**Logs** : 

Logging is sent to syslogd.

**Installing** :

You need python flask library

To install it under ubuntu :

    apt-get install python-flask

 To use this from Postfix SMTPD, use in /etc/postfix/main.cf:

    smtpd_recipient_restrictions =
    ...
    reject_unlisted_recipient,
    check_policy_service inet:127.0.0.1:1143
    permit_sasl_authenticated,
    reject_unauth_destination
    ...

This policy should be included after reject_unlisted_recipient if used,
but before any permit rules or maps which return OK.

**Testing** :

To test this script by hand, execute:

   % telnet localhost 1143

Each query is a bunch of attributes. Order does not matter.

    request=smtpd_access_policy
    recipient=bar@foo.tld
    [empty line]

The policy server script will answer in the same style, with an
attribute list followed by a empty line:

    action=dunno
    [empty line]
