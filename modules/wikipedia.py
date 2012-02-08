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


SNIPPET_REPL = {
	"<span class='searchmatch'>" : "\x034",
	"</span>" : "\x03",
	"<b>" : "",
	"</b>" : "",
	"  " : " ",
	"…" : "...",
}

# XChats URL-Scanner bricht fäschlicher Weise an manchen Zeichen ab, die in 
# Wikipedia-Links aber recht häufig sind, also prozentkodieren wir die:
URL_REPL = {
	"(" : "%28",
	")" : "%29",
}

def wiki_wiki( plugin, connection, channel, source_nick, args ):
	if not args:
		connection.action( channel, "reagiert z.B. auf: !wiki suchbegriff   ODER   !wiki suchbegriff -ausschlusskriterium" )
		return
	suggestion = None
	try:
		query = urllib.parse.urlencode( { "srsearch" : args } )
		resp = urllib.request.urlopen( "http://de.wikipedia.org/w/api.php?format=xml&action=query&list=search&%(query)s&srprop=snippet&srlimit=1" % locals() )
		result = resp.readall().decode("utf-8")
		tree = etree.parse( io.StringIO(result) )
		hits = None
		try:
			hits = int(tree.xpath( "//searchinfo/@totalhits")[0] )
		except Exception as e:
			print( e )
		try:
			suggestion = tree.xpath( "//searchinfo/@suggestion" )[0]
		except Exception as e:
			print( e )
		title = tree.xpath( "//search/p/@title" )[0]
		snippet = tree.xpath( "//search/p/@snippet" )[0]
		for key in SNIPPET_REPL:
			snippet = snippet.replace( key, SNIPPET_REPL[key] )
		query = urllib.parse.urlencode( { "titles" : title } )
		resp = urllib.request.urlopen( "http://de.wikipedia.org/w/api.php?format=xml&action=query&%(query)s&prop=info&inprop=url" % locals() )
		result = resp.readall().decode("utf-8")
		tree = etree.parse( io.StringIO(result) )
		url = tree.xpath( "//page/@fullurl" )[0]
		for key in URL_REPL:
			url = url.replace( key, URL_REPL[key] )
		if url[-1] == ".":
			# HACK: verhindern, dass ein abschließender Punkt von möchtegern-
			# intelligenten URL-Scannern abgeschnitten wird:
			url = url[:-1]+"%2e"
		touched = None
		try:
			touched = tree.xpath( "//page/@touched" )[0]
		except Exception as e:
			print( e )
		connection.action( channel, "fand: %(title)s: %(snippet)s   [ %(url)s ]" % locals() )
	except Exception as e:
		print( e )
		if suggestion:
			connection.action( channel, "überlegt ob du vielleicht \"%(suggestion)s\" meintest..." % locals() )
		else:
			connection.action( channel, "hat dazu auf Wikipedia nichts gefunden." )


def handle_event( plugin, connection, event ):
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
			if "wiki_"+command in globals() and approve_action():
				globals()["wiki_"+command]( plugin, connection, channel, source_nick, cargs )


HANDLERS = {
	"privmsg" : handle_event,
	"pubmsg" : handle_event
}

