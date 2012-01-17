import re, random

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
	print( "in handle_error" )
	if "closing link" in event.target().lower():
		print( "in closing link" )
		# FIXME: Wird hierbei nicht die TCP-Session terminiert?
		#	Wieso generiert irclib dabei KEINEN disconnect-Event?
		handle_disconnect( plugin, connection, event )

def handle_disconnect( plugin, connection, event ):
	print( "in handle_disconnect" )
	channel_names = []
	if connection in channels_by_con_and_name:
		print( "connection in channels_by_con_and_name" )
		channel_names = [k for k in channels_by_con_and_name[ connection ].keys()]
		del channels_by_con_and_name[ connection ]
	# Mit Join-Liste der aktuellen Channel-Namen neu verbinden:
	plugin.bot.reconnect( channel_names )

HANDLERS = {
	"namreply" : handle_namreply,
	"join" : handle_joinpart,
	"part" : handle_joinpart,
	"quit" : handle_joinpart,
	"nick" : handle_nick_change,
	"error" : handle_error,
	"disconnect" : handle_disconnect,
}

