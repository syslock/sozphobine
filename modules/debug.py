import re

OWNER_MASK = "syslock!syslock@.*"

def handle_event( plugin, connection, event ):
	source = event.source()
	source_nick = source.split("!")[0]
	args = event.arguments()
	command = re.match( "^!(\S+)", args[0] )
	cargs = re.findall( "\s+(\S+)", args[0] )
	if command:
		command = command.group(1)
	if re.match( OWNER_MASK, source ):
		if command:
			result = re.findall( "^((?:re|un)?load)$", command )
			if result and len(cargs)==1:
				plugin_cmd = result[0]
				plugin_name = cargs[0]
				print( "INFO: %s - %sing %s." % (__name__,plugin_cmd,plugin_name) )
				plugin_func = getattr( plugin.bot,plugin_cmd+"_plugin" )
				plugin_func( plugin_name )
		if command=="plugins":
			connection.privmsg( source_nick, ", ".join(plugin.bot.plugins.keys()) )
		if command=="join" and len(cargs)==1:
			plugin.bot.connection.join( cargs[0] )
		if command=="part" and len(cargs)==1:
			plugin.bot.connection.part( cargs[0] )
		if command=="plugin":
			if len(cargs)==3 and cargs[1]=="get":
				text = str(None)
				try:
					text = str( getattr(plugin.bot.plugins[cargs[0]].module, cargs[2]) )
				except Exception as e:
					text = str(e)
				connection.privmsg( source_nick, text )
			if len(cargs)==4 and cargs[1]=="set":
				try:
					setattr( plugin.bot.plugins[cargs[0]].module, cargs[2], eval(cargs[3]) )
				except Exception as e:
					connection.privmsg( source_nick, str(e) )
		if command=="disconnect":
			connection.disconnect( "requested" )
		if command=="quit":
			connection.quit( "requested" )

HANDLERS = {
	"privmsg" : handle_event,
	"pubmsg" : handle_event
}

