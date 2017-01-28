Script for broadcasting messages in ICQ.
==============================================

Installation
----------------

Installation on clear machine (assumes you have python2.7 installed)::

    sudo apt-get install python-twisted

Script was checked on Linux machine (Ubuntu 14.04 LTS). It can be ported on Windows with minimal changes.

Usage example::

    If you send only one message:
        python main.py -u 77733322 -p **** -m "test message goes here"

    If you want send messages from file:
        python main.py -u <UIN> -p <PASSWORD> --messages-file <path to messages.txt>

parameters:

	--user  			required=true 
	--password  		required=true
	--messages-file 	Path to messages.txt file which contains messages: one message per line
	--message 			Text message which should be sent
	--sleep-time		sleep intervals in minutes
	--groups-only		Broadcast groups only


