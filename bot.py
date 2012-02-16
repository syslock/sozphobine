import time, imp
from irclib3 import irclib


def is_on_channel( plugin, connection, channel, nick ):
	return "monitor" not in plugin.bot.plugins \
			or channel in plugin.bot.plugins["monitor"].module\
				.get_channels_by_con_and_nick( connection, nick )


def same_nick( nick1, nick2 ):
	return nick1.strip().lower()==nick2.strip().lower()



class Timer:
	def __init__( self, delay, callback, callargs, loop=False ):
		self.time = time.time()
		self.delay = delay
		self.callback = callback
		self.callargs = callargs
		self.loop = loop
	def process_once( self, plugin ):
		if time.time()-self.time > self.delay:
			self.time += self.delay # für Schleifen
			self.callback( self, *self.callargs )
			return not self.loop
		else:
			return False


class Plugin:
	def __init__( self, name, bot=None ):
		self.name = name
		self.bot = bot
		self.module = __import__( "modules."+self.name, fromlist=[self.name] )
		self.handlers = {}
		self.subscribe_events()
		self.timers = []
		if "init" in dir(self.module):
			try:
				self.module.init( self )
			except Exception as e:
				print( "FAIL: Initialisierung von %s: %s" %(self.name,str(e)) )
				if hasattr(self.module,"DEBUG") and self.module.DEBUG:
					raise
	def reload( self ):
		self.unsubscribe_events()
		self.module = imp.reload( self.module )
		self.subscribe_events()
	def reinit( self ):
		if "reinit" in dir(self.module):
			try:
				self.module.reinit( self )
			except Exception as e:
				print( "FAIL: Reinitialisierung von %s: %s" %(self.name,str(e)) )
				if hasattr(self.module,"DEBUG") and self.module.DEBUG:
					raise
	def __handle_event__( self, con, event ):
		if event.eventtype() in self.handlers:
			try:
				self.handlers[event.eventtype()]( self, con, event )
			except Exception as e:
				print( "FAIL: Eventbehandlung in %s: %s" % (self.name,str(e)) )
				if hasattr(self.module,"DEBUG") and self.module.DEBUG:
					raise
				else:
					self.reload()
		else:
			print( "WARN: Unhandled event %s in Plugin %s" % (event.eventtype(), self.name) )
	def subscribe_events( self ):
		self.handlers = {}
		for event_key in self.module.HANDLERS:
			self.bot.irc.add_global_handler( event_key, self.__handle_event__, priority=self.bot.next_handler_priority )
			function = self.module.HANDLERS[event_key]
			self.handlers[ event_key ] = function
		self.bot.next_handler_priority += 1
	def unsubscribe_events( self ):
		self.handlers = {}
		for event_key in self.module.HANDLERS:
			self.bot.irc.remove_global_handler( event_key, self.__handle_event__ )
	def process_once( self ):
		new_timers = []
		for timer in self.timers:
			ready = True
			try:
				ready = timer.process_once( self )
			except Exception as e:
				print( "FAIL: Zeitereignis in %s: %s" % (self.name,str(e)) )
				if hasattr(self.module,"DEBUG") and self.module.DEBUG:
					raise
				else:
					self.reload()
			if not ready:
				new_timers.append( timer )
		self.timers = new_timers
		if "process_once" in dir(self.module):
			try:
				self.module.process_once( self )
			except Exception as e:
				print( "FAIL: Hintergrundprozess in %s: %s" % (self.name,str(e)) )
				if hasattr(self.module,"DEBUG") and self.module.DEBUG:
					raise
				else:
					self.reload()


class Bot:
	def __init__( self, host, nick, port=6667 ):
		self.host = host
		self.nick = nick
		self.port = port
		irclib.DEBUG = True
		self.irc = irclib.IRC()
		self.connection = self.irc.server()
		self.connection.connect( self.host, self.port, self.nick )
		self.plugins = {}
		self.next_handler_priority = 0
		self.auto_rejoin_channels = set()
	def run( self, stop_conditions=[] ):
		while True:
			stop = False
			for stop_condition in stop_conditions:
				stop = stop or stop_condition()
			if stop:
				break
			self.irc.process_once()
			for plugin in self.plugins.values():
				plugin.process_once()
			time.sleep(0.1)
	def reconnect( self ):
		self.connection.connect( self.host, self.port, self.nick )
	def load_plugin( self, name ):
		if name not in self.plugins:
			self.plugins[ name ] = Plugin( name, bot=self )
	def unload_plugin( self, name ):
		if name in self.plugins:
			self.plugins[ name ].unsubscribe_events()
			del self.plugins[ name ]
	def reload_plugin( self, name ):
		if name in self.plugins:
			self.plugins[ name ].reload()
		else:
			self.load_plugin( name )
	def reinit_plugins( self ):
		for name in self.plugins:
			self.plugins[ name ].reinit()
	def join( self, channel_name, auto_rejoin=True ):
		if auto_rejoin:
			self.auto_rejoin_channels.add( channel_name )
		self.connection.join( channel_name )
	def rejoin( self ):
		for channel in self.auto_rejoin_channels:
			self.connection.join( channel )

