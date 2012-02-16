import re, random, time
from bot import Timer

class User:
	def __init__( self, full_name ):
		parts = full_name.split("!")
		self.nick = parts[0].strip().lower()
		if len(parts)>1:
			self.mask = parts[1]
		else:
			self.mask = None

class Channel:
	def __init__( self, connection, name ):
		self.connection = connection
		self.name = name
		self.users = {}
	def add_user( self, user ):
		self.users[ user.nick ] = user
	def del_user( self, user ):
		if user.nick in self.users:
			del self.users[ user.nick ]
	def get_user( self, user ):
		if user.nick in self.users:
			return self.users[ user.nick ]
		else:
			return None

channels_by_con_and_name = {}

def register_channel( connection, channel_name ):
	if not connection in channels_by_con_and_name:
		channels_by_con_and_name[ connection ] = {}
	if not channel_name in channels_by_con_and_name[ connection ]:
		channel = Channel( connection, channel_name )
		channels_by_con_and_name[ connection ][ channel.name ] = channel

def handle_joinpart( plugin, connection, event ):
	channel_name = event.target()
	if channel_name: # quit hat keinen channel_name
		register_channel( connection, channel_name )
	user_full_name = event.source()
	user = User( user_full_name )
	if event.eventtype() == "join":
		# joinende Nutzer hinzufügen:
		channels_by_con_and_name[ connection ][ channel_name ].add_user( user )
		if user.nick == connection.get_nickname().strip().lower():
			# Wenn Bot selber joint, Namensliste für Channel abfragen:
			connection.names( [channel_name] )
	elif event.eventtype() == "part":
		# partende Nutzer löschen:
		channels_by_con_and_name[ connection ][ channel_name ].del_user( user )
		if user.nick == connection.get_nickname().strip().lower():
			# Wenn Bot selber partet, Channel entfernen:
			del channels_by_con_and_name[ connection ][ channel_name ]
	elif event.eventtype() == "quit":
		if user.nick == connection.get_nickname().strip().lower():
			# Wenn Bot selber quittet, alle zugehörigen Channels entfernen:
			del channels_by_con_and_name[ connection ]
		else:
			# Sonst Nutzer aus allen Channels der Connection bereinigen:
			for channel in channels_by_con_and_name[ connection ].values():
				channel.del_user( user )
		
def handle_namreply( plugin, connection, event ):
	args = event.arguments()
	if not args or args[0]!="=":
		return # Should not happen?
	channel_name = args[1]
	register_channel( connection, channel_name )
	raw_nicks = args[2].split()
	for raw_nick in raw_nicks:
		if raw_nick[0] in ["@","+","%"]:
			nick = raw_nick[1:]
		else:
			nick = raw_nick
		user = User( nick )
		channels_by_con_and_name[ connection ][ channel_name ].add_user( user )

def handle_nick_change( plugin, connection, event ):
	# Falls wir die Verbindung nicht kennen, sind wir hier verloren, 
	# weil kein Kanalname an der Nachricht steht: 
	if connection in channels_by_con_and_name:
		ref_old = User( event.source() )
		ref_new = User( event.target() )
		for channel in channels_by_con_and_name[ connection ].values():
			old_user = channel.get_user( ref_old )
			if old_user:
				channel.del_user( old_user )
				new_user = old_user
				new_user.nick = ref_new.nick
				if ref_new.mask:
					new_user.mask = ref_new.mask
				elif ref_old.mask:
					new_user.mask = ref_old.mask
				channel.add_user( new_user )				

# Gibt Kanalnamen zurück die, dieser Verbindung und dem Nick zugeordnet werden konnten.
def get_channels_by_con_and_nick( connection, nick ):
	channel_names = []
	if connection in channels_by_con_and_name:
		for channel in channels_by_con_and_name[ connection ].values():
			if nick.strip().lower() in channel.users:
				channel_names.append( channel.name )
	return channel_names

def handle_error( plugin, connection, event ):
	if "closing link" in event.target().lower():
		# FIXME: Wird hierbei nicht die TCP-Session terminiert?
		#	Wieso generiert irclib dabei KEINEN disconnect-Event?
		if connection.connected:
			connection.disconnect( "link error" )

def handle_disconnect( plugin, connection, event ):
	if connection in channels_by_con_and_name:
		del channels_by_con_and_name[ connection ]
	plugin.welcome_received = False

CLIENT_PING_PERIOD = 60*5 # Server alle n Minuten pingen
CLIENT_PING_TIMEOUT = 60*3 # Verbindung trennen, wenn PONG m Minuten ausbleibt
def client_ping( timer, plugin ):
	global CLIENT_PING_TIMEOUT
	plugin.bot.connection.ping( "%d" % time.time() )
	# PING-Timeout programmieren:
	plugin.timers.append( Timer(delay=CLIENT_PING_TIMEOUT,
								callback=client_ping_timeout,
								callargs=(plugin,)) )

def client_ping_timeout( timer, plugin ):
	global CLIENT_PING_TIMEOUT
	print( "%s - Client-PING-Timeout! (%ds)" % (time.ctime(), CLIENT_PING_TIMEOUT) )
	plugin.bot.connection.disconnect( "client ping timeout" )

def handle_pong( plugin, connection, event ):
	# Alle Client-PING-Timeouts löschen:
	for i in range(len(plugin.timers)):
		timer = plugin.timers[i]
		if timer.callback == client_ping_timeout:
			print( "%s - Lösche Client-PING-Timeout nach %.3fs" % (time.ctime(), time.time()-timer.time) )
			del plugin.timers[i]

def handle_nicknameinuse( plugin, connection, event ):
	print( "%s - %s" % (time.ctime(), str(event.arguments())) )
	base_nick, current_num = re.findall( "^(.*?)([0-9]*)$", event.arguments()[0] )[0]
	current_num = current_num and (int(current_num) + 1) or 2
	new_nick = base_nick + str(current_num)
	connection.nick( new_nick )	

def handle_welcome( plugin, connection, event ):
	plugin.welcome_received = True

def init( plugin ):
	plugin.welcome_received = False
	# Client-PING-Timer programmieren, aber sicherstellen, 
	# dass nur einer existiert:
	ping_timer = None
	for timer in plugin.timers:
		if timer.callback == client_ping:
			if ping_timer and ping_timer.loop and timer.loop:
				timer.loop = False
			else:
				ping_timer = timer
	global CLIENT_PING_PERIOD
	if not ping_timer:
		plugin.timers.append( Timer(delay=CLIENT_PING_PERIOD,
									callback=client_ping,
									callargs=(plugin,),
									loop=True) )

HANDLERS = {
	"namreply" : handle_namreply,
	"join" : handle_joinpart,
	"part" : handle_joinpart,
	"quit" : handle_joinpart,
	"nick" : handle_nick_change,
	"error" : handle_error,
	"disconnect" : handle_disconnect,
	"pong" : handle_pong,
	"nicknameinuse" : handle_nicknameinuse,
	"welcome" : handle_welcome
}

