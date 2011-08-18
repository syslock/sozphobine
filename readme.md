# irclib3 -- Internet Relay Chat (IRC) protocol client library

This library is intended to encapsulate the IRC protocol at a quite
low level.  It provides an event-driven IRC client framework.  It has
a fairly thorough support for the basic IRC protocol, CTCP and DCC
connections.

In order to understand how to make an IRC client, I'm afraid you more
or less must understand the IRC specifications.  They are available
[here](http://www.irchelp.org/irchelp/rfc/).

This is a work in progress port from Python 2 to Python 3.

## Development

It imports! Syntactically, to the interpreter, it looks fine. So far, I've fix the handling and raising of exceptions to be Python 3 compatible, as well as encoding strings to UTF-8.
What actually works? Who knows -- hopefully it won't take too long before things start coming together smoothly. 

## This project sucks!

It sure does! The project's in very early development and it's basically a learning project for me, but in the end I hope to have a beneficial product.
Send some commits this way and lets improve it for everybody. There should probably be a rewrite of this library, however, no new code exists yet that covers as much as the original irclib.
