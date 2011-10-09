# irclib3
Internet Relay Chat (IRC) protocol client library

This library is intended to encapsulate the IRC protocol at a quite
low level.  It provides an event-driven IRC client framework.  It has
a fairly thorough support for the basic IRC protocol, CTCP and DCC
connections.

In order to understand how to make an IRC client, I'm afraid you more
or less must understand the IRC specifications.  They are available
[here](http://www.irchelp.org/irchelp/rfc/).

This is a port from Python 2 to Python 3 forked from irclib 0.4.8.

## Development

* fixed the handling and raising of exceptions
* fixed print functions
* messages default to UTF-8, but can be changed to whatever
* switched to new string.format() syntax


## I WANT YOU

IT WORKS! Use it! Report anything wrong you can find and help the project out!

