from bot import Timer


# (server, ns_mask) : (nick, password)
NICKSERV_ACCOUNTS = {}


control_timer = None
def init( plugin ):
	global control_timer
	control_timer =  Timer( 5, check_nickserv_status, (plugin,), loop=True )
	plugin.timers.append( control_timer )


def check_nickserv_status( plugin ):
	if plugin.bot.connection.get_nickname()!=plugin.bot.nick:
		pass # TODO Nick wechseln
	else:
		plugin.bot.connection.privmsg( "nickserv", "status" )


password_timer = None
def handle_notice( plugin, connection, event ):
	global password_timer, control_timer
	source_mask = event.source()
	source_nick = source_mask.split("!")[0]
	if source_nick.lower()=="nickserv":
		args = event.arguments()
		words = args and args[0].split() or []
		if len(words)==3 and words[0].lower()=="status":
			status_nick = words[1]
			status = int(words[2])
			if status not in [2,3] and not password_timer:
				password_timer = Timer( 1, send_nickserv_password, 
					(plugin,connection, source_nick, source_mask) )
				plugin.timers.append( password_timer )
			elif control_timer:
				control_timer.loop = False

HANDLERS = { "privnotice" : handle_notice }



def send_nickserv_password( plugin, connection, nickserv_nick, nickserv_mask ):
	global password_timer, NICKSERV_ACCOUNTS
	password_timer = None
	account_key = ( connection.server, nickserv_mask )
	if account_key in NICKSERV_ACCOUNTS:
		account_nick, account_password = NICKSERV_ACCOUNTS[ account_key ]
		if connection.get_nickname() == plugin.bot.nick == account_nick:
			connection.privmsg( nickserv_nick, "id "+account_password )
		else:
			print( "FAIL: in send_nickserv_password: nickname missmatch: %s, %s, %s" \
				% (connection.get_nickname(), plugin.bot.nick, account_nick) )
	else:
		print( "FAIL: in send_nickserv_password: no nickserv account for key: %s" \
			% (str(account_key)) )

