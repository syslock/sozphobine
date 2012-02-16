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
		resp = urllib.request.urlopen( "http://de.wikipedia.org/w/api.php?format=xml&action=query&list=search&%(query)s&srprop=snippet|redirecttitle&srlimit=10" % locals() )
		result = resp.readall().decode("utf-8")
		tree = etree.parse( io.StringIO(result) )
		hits = 0
		try:
			hits = int( tree.xpath("//searchinfo/@totalhits")[0] )
		except Exception as e:
			print( "Keine Trefferanzahl für \"%(args)s\"" % locals() )
		try:
			suggestion = tree.xpath( "//searchinfo/@suggestion" )[0]
			print( "Suchvorschlag für \"%(args)s\": \"%(suggestion)s\"" % locals() )
			if suggestion.lower()==args.lower():
				print( "...ignoriere." )
				suggestion = None
		except Exception as e:
			pass
		titles = tree.xpath( "//search/p/@title" )
		snippets = tree.xpath( "//search/p/@snippet" )
		if not titles:
			raise Exception( "Kein Treffer in Wikisuche nach \"%(args)s\"" % locals() )
		candidates = []
		for i in range(len(titles)):
			title = titles[i]
			redirect_title = ""
			try:
				redirect_title = tree.xpath( "//search/p[@title='%(title)s']/@redirecttitle" % locals() )[0]
				print( "Weiterleitung zu \"%(title)s\" von \"%(redirect_title)s\"" % locals() )
			except Exception as e:
				pass # häufig
			matching_title_words = 0
			matching_redirect_words = 0
			for word in args.lower().split():
				if word in title.lower():
					#print( "%(word)s in: %(title)s" % locals() )
					matching_title_words += 1
				if word in redirect_title.lower():
					#print( "%(word)s in: %(redirect_title)s" % locals() )
					matching_redirect_words += 1
			candidates.append( (-matching_title_words,len(title),i,"") )
			if redirect_title:
				candidates.append( (-matching_redirect_words,len(redirect_title),i,redirect_title) )
		#print( candidates )
		choice = sorted( candidates )[0]
		n = choice[2] # ID des besten Treffers
		title = titles[n] # Titel des besten Treffers
		snippet = snippets[n] # Snippet des besten Treffers
		redirect = choice[3] # ggF. Redirect
		if redirect:
			redirect = redirect + " => "
		n += 1 # intuitive Zählung fängt bei 1 an
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
		connection.action( channel, "fand %(redirect)s%(title)s: %(snippet)s   [ %(url)s ]   (Treffer# %(n)d/%(hits)d)" % locals() )
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
	else:
		channel = source_nick
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
	"pubmsg" : handle_event,
	"privnotice" : handle_event,
}

