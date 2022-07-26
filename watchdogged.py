#!/usr/bin/python3
# vim: ts=4 sts=4 sw=4 ft=python expandtab :

"""Welcome to a pretty complex watchdog example.

Unlike most examples, this does some error checking, and generally ought to
pass a code review without too much hassle.

Change the PROBABILITY below to get some interesting numbers.



watchdogged.py; python teaching code for how to use the systemd watchdog  
Copyright (C) 2015 D.S. Ljungmark, Modio AB  

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
print ("imported " + __name__)

import logging
import random
import socket
import time
import sys
import os

# All singletons are prefixed the
theLog = logging.getLogger(__name__)


def watchdog_period():
    """Return the time (in seconds) that we need to ping within."""
    val = os.environ.get("WATCHDOG_USEC", None)
    if not val:
        return None
    return int(val)/1000000


def notify_socket(clean_environment=True):
    """Return a tuple of address, socket for future use.

    clean_environment removes the variables from env to prevent children
    from inheriting it and doing something wrong.
    """
    _empty = None, None
    address = os.environ.get("NOTIFY_SOCKET", None)
    if clean_environment:
        address = os.environ.pop("NOTIFY_SOCKET", None)

    if not address:
        return _empty

    if len(address) == 1:
        return _empty

    if address[0] not in ("@", "/"):
        return _empty

    if address[0] == "@":
        address = "\0" + address[1:]

    # SOCK_CLOEXEC was added in Python 3.2 and requires Linux >= 2.6.27.
    # It means "close this socket after fork/exec()
    try:
        sock = socket.socket(socket.AF_UNIX,
                             socket.SOCK_DGRAM | socket.SOCK_CLOEXEC)
    except AttributeError:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

    return address, sock


def sd_message(address, sock, message):
    """Send a message to the systemd bus/socket.

    message is expected to be bytes.
    """
    if not (address and sock and message):
        return False
    assert isinstance(message, bytes)

    try:
        retval = sock.sendto(message, address)
    except socket.error:
        return False
    return (retval > 0)


def watchdog_ping(address, sock):
    """Helper function to send a watchdog ping."""
    message = b"WATCHDOG=1"
    return sd_message(address, sock, message)


def systemd_ready(address, sock):
    """Helper function to send a ready signal."""
    message = b"READY=1"
    theLog.debug("Signaling system ready")
    return sd_message(address, sock, message)


def systemd_stop(address, sock):
    """Helper function to signal service stopping."""
    message = b"STOPPING=1"
    return sd_message(address, sock, message)


def systemd_status(address, sock, status):
    """Helper function to update the service status."""
    message = ("STATUS=%s" % status).encode('utf8')
    return sd_message(address, sock, message)


#def print_err(msg):
#    """Print an error message to STDERR and quit."""
#    print(msg, file=sys.stderr)
#    sys.exit(1)


def mainloop(notify, period, probability):
    """A simple mainloop, spinning 100 times.

    Uses the probability flag to test how likely it is to cause a
    watchdog error.
    """
    systemd_status(*notify,
                   status="Mainloop started, probability: %s" % probability)

    for x in range(100):
        watchdog_ping(*notify)
        theLog.debug("Sending Watchdog ping: %s" % x)
        time.sleep(period)
        if random.random() < probability:
            systemd_status(*notify, status=b"Probability hit, sleeping extra")
            theLog.info("Sleeping extra, watch for triggered watchdog")
            time.sleep(1)

    theLog.info("Orderly shutdown")
    systemd_status(*notify, status=b"Shutting down")
    systemd_stop(*notify)


def get_probability():
    """Grab the probability from the environment.

    Return it if set, otherwise falls back to 0.01
    """
    prob = os.environ.get("PROBABILITY", "0.01")
    return float(prob)


if __name__ == "__main__":
    # Get our settings from the environment
    notify = notify_socket()
    period = watchdog_period()
    probability = get_probability()
    # Validate some in-data
    if not notify[0]:
        print("No notification socket, not launched via systemd?")
        sys.exit(1)

    if not period:
        print("No watchdog period set in the unit file.")
        sys.exit(1)

    # Start processing
    systemd_status(*notify, status=b"Initializing")

    logging.basicConfig()
    theLog.setLevel(logging.DEBUG)

    # Cut off a bit from the period to make the ping/Execution time work
    period -= 0.01

    theLog.info("We have to ping every: {} seconds".format(period))
    theLog.info("Signalling ready")
    systemd_ready(*notify)

    mainloop(notify, period, probability)


