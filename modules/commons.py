import re, time, io, random
import urllib, urllib.request, urllib.parse
from lxml import etree


last_action_time = 0
ACTION_TIMEOUT = 1.5

def approve_action():
	global last_action_time
	if last_action_time + ACTION_TIMEOUT > time.time():
		return False
	else:
		last_action_time = time.time()
		return True


# XChats URL-Scanner bricht fäschlicher Weise an manchen Zeichen ab, die in 
# Wikipedia-Links aber recht häufig sind, also prozentkodieren wir die:
URL_REPL = {
	"(" : "%28",
	")" : "%29",
}

def commons_bild( plugin, connection, channel, source_nick, args ):
	if not args:
		connection.action( channel, "reagiert auf: !bild suchbegriff" )
		return
	suggestion = None
	try:
		query = urllib.parse.urlencode( { "search" : args } )
		resp = urllib.request.urlopen( "http://commons.wikimedia.org/w/api.php?format=xml&action=opensearch&%(query)s&namespace=6&limit=100" % locals() )
		result = resp.readall().decode("utf-8")
		result = re.sub( r'xmlns="[^"]*"', '', result ) # try to strip namespaces
		open( "/tmp/commons_resp.dmp", "wb" ).write( result.encode("utf-8") )
		tree = etree.parse( io.StringIO(result) )
		items = tree.xpath("//Section/Item")
		hits = len(items)
		item_no = random.randint( 0, hits-1 )
		item = items[item_no]
		url = item.xpath("string(.//Url)")
		connection.action( channel, "fand %(url)s (Treffer# %(item_no)d/%(hits)d)" % locals() )
	except Exception as e:
		print( e )
		connection.action( channel, "zuckt nur mit den Schultern." )
commons_img = commons_image = commons_bild


def handle_event( plugin, connection, event ):
	source = event.source()
	source_nick = source.split("!")[0]
	target = event.target()
	channel = None
	if target[0]=='#':
		channel = target
	else:
		channel = source_nick
	if channel:
		args = event.arguments()
		result = re.findall( "^!(\S+)\s*(.*)$", args[0] )
		if result:
			command, cargs = result[0]
			cargs = cargs.strip()
			if "commons_"+command in globals() and approve_action():
				globals()["commons_"+command]( plugin, connection, channel, source_nick, cargs )


HANDLERS = {
	"privmsg" : handle_event,
	"pubmsg" : handle_event,
	"privnotice" : handle_event,
}

