# Copyright (C) 1999--2002  Joel Rosdahl
# Copyright (C) 2011 Jimmy Zelinskie
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA
#
# Rewritten and ported to Python 3 by
# Jimi <jimmyzelinskie@gmail.com>
#

"""irclib -- Internet Relay Chat (IRC) protocol client library.

This library is intended to encapsulate the IRC protocol at a quite
low level.  It provides an event-driven IRC client framework.  It has
a fairly thorough support for the basic IRC protocol, CTCP, DCC chat,
but DCC file transfers is not yet supported.

In order to understand how to make an IRC client, I'm afraid you more
or less must understand the IRC specifications.  They are available
here: [IRC specifications].

The main features of the IRC client framework are:

  * Abstraction of the IRC protocol.
  * Handles multiple simultaneous IRC server connections.
  * Handles server PONGing transparently.
  * Messages to the IRC server are done by calling methods on an IRC
    connection object.
  * Messages from an IRC server triggers events, which can be caught
    by event handlers.
  * Reading from and writing to IRC server sockets are normally done
    by an internal select() loop, but the select()ing may be done by
    an external main loop.
  * Functions can be registered to execute at specified times by the
    event-loop.
  * Decodes CTCP tagging correctly (hopefully); I haven't seen any
    other IRC client implementation that handles the CTCP
    specification subtilties.
  * A kind of simple, single-server, object-oriented IRC client class
    that dispatches events to instance methods is included.

Current limitations:

  * The IRC protocol shines through the abstraction a bit too much.
  * Data is not written asynchronously to the server, i.e. the write()
    may block if the TCP buffers are stuffed.
  * There are no support for DCC file transfers.
  * The author haven't even read RFC 2810, 2811, 2812 and 2813.
  * Like most projects, documentation is lacking...

.. [IRC specifications] http://www.irchelp.org/irchelp/rfc/
"""

import bisect
import re
import select
import socket
import string
import sys
import time
import types

VERSION = 0, 0, 1
DEBUG = 0

class IRCError(Exception):
  """Represents an IRC exception."""
  pass

class IRC:
  """Class that handles one or several IRC server connections.

  When an IRC object has been instantiated, it can be used to create
  Connection objects that represent the IRC connections. The
  responsibility of the IRC object is to provide an event-driven
  framework for the connections and to keep the connections alive.
  It runs a select loop to poll each connection's TCP socket and
  hands over the sockets with incoming data for processing by the
  corresponding connection.

  The methods of most interest for an IRC client writer are server,
  add_global_handler, remove_global_handler, execute_at,
  execute_delayed, process_once, and process_forever.

  Here is an example:

    irc = irc.lib.IRC()
    server = irc.server()
    server.connect(\"irc.some.where\", 6667, \"my_nick\")
    server.privmsg(\"friends_nick\", \"Hi there!\")
    irc.process_forever()

  This will connect to the IRC server irc.some.where on port 6667
  using the nickname my_nick and send the message \"Hi there!\"
  to the nickname friends_nick. The connection remains indefinitely
  due to the process_forever() function call.
  """

  def __init__(self, fn_to_add_socket=None,
               fn_to_remove_socket=None,
               fn_to_add_timeout=None):
    """Constructor for IRC object.
    
    Optional arguments are fn_to_add_socket, fn_to_remove_socket
    and fn_to_add_timeout. THe first two specific functions that
    will be called with a socket object as argument when the IRC
    object wants to be notified (or stop being notified) of data
    coming on a new socket. When new data arrives, the method
    process_data should be called. Similarly, fn_to_add_timeout
    is called with a number of seconds (a floating point number)
    as the first argument when the IRC object wants to receive a
    notification (by calling the process_timeout method). So, if
    e.g. the argument is 42.17, the object wants the
    process_timeout method to be called after 42 seconds and 170
    milliseconds.

    The three arguments mainly exist to be able to use an external
    main loop (for example Tkinter's or PyGTK's main app loop)
    instead of calling the process_forever method.

    An alternative is to just call ServerConnection.process_once()
    once in a while.
    """

    if fn_to_add_socket and fn_to_remove_socket:
      self.fn_to_add_socket = fn_to_add_socket
      self.fn_to_remove_socket = fn_to_remove_socket
    else:
      self.fn_to_add_socket = None
      self.fn_to_remove_socket = None

    self.fn_to_add_timeout = fn_to_add_timeout
    self.connections = []
    self.handlers = {}
    self.delayed_commands = [] #tuple format: (time, function, args)


    self.add_global_handler("ping",_ping_ponger, -42)

  def server(self):
    """Creates and returns a ServerConncetion object."""

    c = ServerConnection(self)
    self.connections.append(c)
    return c

  def process_data(self, sockets):
    """Called when there is more data to read on connection sockets.

    Arguments:
      
      sockets -- A list of socket objects

    See documentation for IRC.__init__.
    """
    t = time.time()
    while self.delayed_commands:
      if t >= self.delayed_commands[0][0]:
        self.delayed_commands[0][1](*self.delayed_commands[0][2])
        del self.delayed_commands[0]
      else:
        break

  def process_once(self, timeout=0):
    """Process data from connections once.

    Arugments:

      timeout -- How long the select() call should wait if no
                 data is available.

    This method should be called periodically to check and process
    incoming data, if there are any. If that doesn't suite your
    implementation, look at the process_forever method.
    """
  
