import re, time, io
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

def osm_osm( *args, **keyargs ): osm_zeig( *args, **keyargs )
def osm_map( *args, **keyargs ): osm_zeig( *args, **keyargs )
def osm_karte( *args, **keyargs ): osm_zeig( *args, **keyargs )
def osm_zeig( plugin, connection, channel, source_nick, args ):
	if not args:
		connection.action( channel, "reagiert auf: !zeig suchbegriff" )
		return
	suggestion = None
	try:
		query = urllib.parse.urlencode( { "q" : args } )
		url = "http://nominatim.openstreetmap.org/search/?%(query)s" % locals()
		print( url )
		resp = urllib.request.urlopen( url )
		result = resp.readall().decode("utf-8")
		# XML-Namespace-Referenz rauspatchen, dar sonst nervige Namespace-Präfixe nutzen müssten oder schlimmeres:
		result = re.sub(r' xmlns="[^"]*"','', result )
		tree = etree.parse( io.StringIO(result) )
		results = tree.xpath( "//div[@class='result']" )
		if not results:
			error = tree.xpath( "//div[@class='noresults']" )
			if error:
				error = " (%s)." % error[0].xpath("string(.)")
			else:
				error = "."
			connection.action( channel, "hat dazu nichts auf openstreetmap.org gefunden"+error )
		else:
			first = results[0]
			name = first.xpath( "string(//span[@class='name'])" )
			pos = first.xpath( "string(//span[@class='latlon'])" )
			connection.action( channel, "fand %(name)s (%(pos)s)   [ %(url)s ]" % locals() )
	except Exception as e:
		print( e )
		connection.action( channel, "hat dazu nichts auf openstreetmap.org gefunden. (Verarbeitungsfehler)" )

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
			if "osm_"+command in globals() and approve_action():
				globals()["osm_"+command]( plugin, connection, channel, source_nick, cargs )


HANDLERS = {
	"privmsg" : handle_event,
	"pubmsg" : handle_event,
	"privnotice" : handle_event,
}

