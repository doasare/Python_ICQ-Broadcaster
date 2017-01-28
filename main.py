#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ICQ bot

import os
import re
import sys
from argparse import ArgumentParser
from pprint import pprint
from twisted.internet.defer import Deferred
from twisted.python.failure import Failure
from twisted.words.protocols import oscar
from twisted.internet import protocol, reactor, defer

import logging

import time

logging.basicConfig(
    level="INFO",
    format='%(asctime)s [%(levelname)s][%(processName)s][%(threadName)s][%(filename)s:%(lineno)s] %(name)s: %(message)s'
)

LOGGER = logging.getLogger("root")

# Server
host = ("login.icq.com", 5190)
icqMode = 1

# Status message
AMSG = "I'm here +)"


class B(oscar.BOSConnection):

    capabilities = [oscar.CAP_CHAT]

    UIN = None  #UIN of profile
    MESSAGES = None #list of messages which should be send to EVERY user in contact list
    SLEEP_TIME = None
    SEND_TO_GROUPS_ONLY = False

    def initDone(self):
        LOGGER.info("Connected to ICQ server(initDone): UIN=%s, HOST=%s, PORT=%s",
                    self.UIN, host[0], host[1])

        self.requestSelfInfo().addCallback(self.gotSelfInfo)
        self.requestSSI().addCallback(self.gotBuddyList)
        self.setAway(AMSG)


    def gotSelfInfo(self, user):
        LOGGER.info("Get current user info(gotSelfInfo): name=%s", user.name)

        self.user = user
        self.name = user.name

    def gotBuddyList(self, l):
        LOGGER.info("Got contacts list(gotBuddyList): %s", l)

        groups = l[0]
        self.userUINs = []

        for group in groups:
            if group.name == "Conferences" or not self.SEND_TO_GROUPS_ONLY:
                self.userUINs += group.users

        LOGGER.info("Got user's UINs: %s", map(lambda u: u.name, self.userUINs))

        self.activateSSI()
        self.setProfile("""ICQBot""")
        self.setIdleTime(0)
        self.clientReady()

        self.messagesCounter = 0

        self.sendToContacts()

    def sendToContacts(self):
        ":rtype: Deferred"
        LOGGER.info("Start send to contacts(sendToContacts)")
        deffereds = []

        for user in self.userUINs:
            for message in self.MESSAGES:
                message = message.decode("utf-8").encode("cp1251")
                newDefer = self.sentIcqMessage(user.name, message)

                assert isinstance(newDefer, Deferred)
                newDefer.addErrback(self.onMessageError, user.name)
                deffereds.append(newDefer)


        return defer.gatherResults(deffereds).addCallback(self.onAllMessagesSent)

    def onMessageError(self, failure, uin):
        ":type: twisted.python.failure.Failure"
        LOGGER.error("Can't send message to uin %s. It looks like you was banned or deleted from this chat.",
                     uin)

    def sentIcqMessage(self, user, message):
        defer = self.sendMessage(user, message=message, wantAck=1, offline=1)
        defer.addCallback(self.onMessageSent)
        return defer

    def onMessageSent(self, data):
        LOGGER.info("Message send: uin=%s", data[0])

    def onAllMessagesSent(self, *a, **k):
        LOGGER.info("All messages has been sent. Schedule next resend in %s minutes", self.SLEEP_TIME)
        reactor.callLater(self.SLEEP_TIME*60, self.sendToContacts)


class OA(oscar.OscarAuthenticator):
    BOSClass = B

def main():

    # first parse args

    parser = ArgumentParser(description="Script for broadcasting messages in ICQ.")

    parser.add_argument("--messages-file", help="Path to messages.txt file which contains messages: one message per line")
    parser.add_argument("-m", "--message", help="Text message which should be sent. You can also specify --messages-file if you want to send bulk of messages")
    parser.add_argument("-u", "--user", help="UIN of user", required=True)
    parser.add_argument("-p", "--password", help="Password from account", required=True)
    parser.add_argument('--sleep-time', help="Time between sending in minutes. By default one hour (60 minutes)",
                        default="60")
    parser.add_argument("--groups-only", action="store_true", help="If flag is present messages will be sent only to groups.")
    parser.add_argument(
        "--log-level",
        help="Logging level, by default is INFO(may be too verbose). Can be one from INFO, WARN, ERROR",
        default="INFO"
    )

    ns = parser.parse_args(sys.argv[1:])

    sleep_time = int(ns.sleep_time)

    LOGGER.setLevel(ns.log_level)

    if not ns.message and not ns.messages_file:
        print >> sys.stderr, "You should specify message or message file!"
        sys.exit(1)

    messages = []
    if ns.messages_file:
        with open(ns.messages_file, "r") as fd:
            text = fd.read()

            messages = [item for item in text.split("\n\n\n") if item]
    else:
        messages = [ns.message]

    # set Oscar parameters
    B.UIN = ns.user
    B.MESSAGES = messages
    B.SLEEP_TIME = sleep_time
    B.SEND_TO_GROUPS_ONLY = ns.groups_only

    def callback(oscarConnection):
        ":type oscarConnection: B"

    d = Deferred()
    d.addCallback(callback)
    protocol.ClientCreator(reactor, OA, ns.user, ns.password, icq=icqMode).connectTCP(*host)
    reactor.run()


if __name__ == '__main__':
    main()
