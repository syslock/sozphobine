import re, sqlite3, time, random
from modules.monitor import User
from bot import is_on_channel, same_nick


DEBUG=False # True = alle Plugin-Exceptions fatal

last_action_time = 0
ACTION_TIMEOUT = 1.5

def approve_action():
	global last_action_time
	if last_action_time + ACTION_TIMEOUT > time.time():
		return False
	else:
		last_action_time = time.time()
		return True


connection = None
def get_connection():
	global connection
	if not connection:
		connection = sqlite3.connect("seen.db")
	return connection


# FIXME: Das sollte nur der Bot-Owner können, wir haben aber noch kein 
# richtiges AAA-Konzept
def seen_initmsgdb( plugin, connection, channel, source_nick, args ):
	con = get_connection()
	c = con.cursor()
	try:
		c.execute( """drop table messages""" )
	except sqlite3.OperationalError as e:
		print( e )
	c.execute( """create table messages (id integer primary key, 
		time integer, author text, recipient text, msg txt, received integer)""" )
	con.commit()
	c.close()


def seen_setmsg( plugin, connection, channel, source_nick, msg ):
	con = get_connection()
	c = con.cursor()
	c.execute( """insert into messages (time,author,recipient,msg,received)
		 values(?,?,?,?,?)""", 
		 (time.time(), source_nick.strip().lower(), "", msg, 0) )
	con.commit()
	c.close()


def seen_getmsg( plugin, connection, channel, source_nick, nick ):
	con = get_connection()
	c = con.cursor()
	c.execute( """select id, time, author, recipient, msg, received 
		from messages where id=(select max(id) from messages 
		where author=? and recipient='')""",
		(nick.strip().lower(),) )
	for row in c:
		_id, _time, _author, _recipient, _msg, _received = row
		_time = time.strftime( '%d.%m.%Y %H:%M:%S',time.localtime( _time ) )
		connection.action( channel, "hat am %(_time)s von %(_author)s folgende, öffentliche Nachricht notiert: %(_msg)s" \
			% locals() )
		c.execute( """update messages set received=received+1 where id=?""", 
			(_id,) )
	con.commit()
	c.close()


# FIXME: Das sollte nur der Bot-Owner können, wir haben aber noch kein 
# richtiges AAA-Konzept
def seen_initseendb( plugin, connection, channel, source_nick, args ):
	con = get_connection()
	c = con.cursor()
	try:
		c.execute( """drop table seen""" )
	except sqlite3.OperationalError as e:
		print( e )
	c.execute( """create table seen (id integer primary key, 
		time integer, nick text, channel text, server txt, eventtype text, msg text)""" )
	con.commit()
	c.close()


def seen_seen( plugin, connection, channel, source_nick, nick ):
	if not nick:
		connection.action( channel, "==>  !seen <nick>  |  !setmsg <deine-nachricht>  |  !getmsg <nick>" )
	elif same_nick( source_nick, nick ):
		connection.action( channel, "glaubt, dass %(source_nick)s an Identitätsstörungen leidet und macht sich unauffällig eine Notiz." % locals() )
	elif is_on_channel( plugin, connection, channel, nick ):
		connection.action( channel, "reicht %(source_nick)s eine Brille und zeigt auf die Besucherliste. %(nick)s ist doch da!" % locals() )
	elif random.randint(1,10)==1:
		connection.action( channel, "findet, dass es in Mecklenburg-Vorpommern schöne Seen gibt, weiß aber nicht was %(nick)s davon hält." % locals() )
	else:
		con = get_connection()
		c = con.cursor()
		# Das Statement generiert durch die Subselect-Konstruktion mit max(id)
		# nur den neuesten Eintrag der auf einen Suchausdruck passt:
		c.execute( """select id, time, nick, eventtype, msg
			from seen where id=(
				select max(id) from seen 
				where nick like ? and channel=? and server=?)""",
			(nick.strip().lower().replace('*','%'),channel,connection.server) )
		for row in c:
			_id, _time, _nick, _eventtype, _msg = row
			_time = time.strftime( '%d.%m.%Y %H:%M:%S',time.localtime( _time ) )
			txt = "hat %(_nick)s zuletzt am %(_time)s gesehen, als sie oder er"
			if _eventtype=="join":
				txt += " den Raum betrat"
			elif _eventtype=="part":
				txt += " den Raum verließ"
			elif _eventtype=="nick":
				txt += " den Namen änderte"
			elif _eventtype=="namreply":
				txt += " hier herumstromerte"
			elif _eventtype=="quit":
				txt += " die Verbindung verlor"
			if _msg:
				txt += " (%(_msg)s)"
			txt += "."
			connection.action( channel, txt % locals() )
		con.commit()
		c.close()


def handle_msg( plugin, connection, event ):
	source = event.source()
	source_nick = source.split("!")[0]
	target = event.target()
	channel = None
	if target[0]=='#':
		channel = target
	if channel:
		args = event.arguments()
		result = re.findall( "^!(\S+)\s*(.*)$", args[0] )
		if result:
			command, cargs = result[0]
			cargs = cargs.strip()
			if "seen_"+command in globals() and approve_action():
				globals()["seen_"+command]( plugin, connection, channel, source_nick, cargs )


def handle_joinpart( plugin, connection, event ):
	channel_name = event.target()
	channel_names = []
	if channel_name: # part/join
		channel_names.append( channel_name )
	else: #quit
		if "monitor" in plugin.bot.plugins:
			monitor = plugin.bot.plugins["monitor"].module
			for channel_name in monitor.channels_by_con_and_name[ connection ]:
				channel_names.append( channel_name )
		else:
			channel_names.append( str(None) )
	user_full_name = event.source()
	user = User( user_full_name )
	msg = event.arguments()
	if msg:
		msg = msg[0].strip()
	else:
		msg = ""
	con = get_connection()
	c = con.cursor()
	for channel_name in channel_names:
		c.execute( """insert into seen (time,nick,channel,server,eventtype,msg)
			 values(?,?,?,?,?,?)""", 
			 (time.time(), user.nick, channel_name, connection.server, 
			 	event.eventtype(), msg) )
	con.commit()
	c.close()


def handle_namreply( plugin, connection, event ):
	args = event.arguments()
	if not args or args[0]!="=":
		return # Should not happen?
	channel_name = args[1]
	raw_nicks = args[2].split()
	con = get_connection()
	c = con.cursor()
	for raw_nick in raw_nicks:
		if raw_nick[0] in ["@","+","%"]:
			nick = raw_nick[1:]
		else:
			nick = raw_nick
		user = User( nick )
		c.execute( """insert into seen (time,nick,channel,server,eventtype,msg)
			 values(?,?,?,?,?,?)""", 
			 (time.time(), user.nick, channel_name, connection.server, 
			 	event.eventtype(), "") )
	con.commit()
	c.close()


def handle_nick_change( plugin, connection, event ):
	# Falls wir die Verbindung nicht kennen, sind wir hier verloren, 
	# weil kein Kanalname an der Nachricht steht, dafür brauchen
	# wir aber das monitor-Plugin:
	if "monitor" in plugin.bot.plugins:
		monitor = plugin.bot.plugins["monitor"].module
		if connection in monitor.channels_by_con_and_name:
			con = get_connection()
			c = con.cursor()
			ref_old = User( event.source() )
			ref_new = User( event.target() )
			for channel in monitor.channels_by_con_and_name[ connection ].values():
				# Wir gehen davon aus, dass seen nach monitor geladen wurde,
				# und entsprechend bereits den neuen Nutzer eingetragen hat
				# (FIXME: Wir sollten statt dessen lieber ein Ereignis beim 
				#  monitor-Plugin abonnieren und hier auswerten...)
				new_user = channel.get_user( ref_new )
				if new_user:
					print( "%s -> %s in #sozphobie" % (ref_old.nick, ref_new.nick) )
					c.execute( """insert into seen (time,nick,channel,server,eventtype,msg)
						 values(?,?,?,?,?,?)""", 
						 (time.time(), ref_old.nick, channel.name, 
						 	connection.server, event.eventtype(), "danach: "+ref_new.nick) )
					c.execute( """insert into seen (time,nick,channel,server,eventtype,msg)
						 values(?,?,?,?,?,?)""", 
						 (time.time(), ref_new.nick, channel.name, 
						 	connection.server, event.eventtype(), "zuvor: "+ref_old.nick) )
			con.commit()
			c.close()
				


HANDLERS = {
	"privmsg" : handle_msg,
	"pubmsg" : handle_msg,
	"namreply" : handle_namreply,
	"join" : handle_joinpart,
	"part" : handle_joinpart,
	"quit" : handle_joinpart,
	"nick" : handle_nick_change,
}

