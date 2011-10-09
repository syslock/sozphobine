import re, random, time
from bot import Timer


last_action_time = 0
ACTION_TIMEOUT = 1.5

def approve_action():
	global last_action_time
	if last_action_time + ACTION_TIMEOUT > time.time():
		return False
	else:
		last_action_time = time.time()
		return True


def is_on_channel( plugin, connection, channel, nick ):
	return "monitor" not in plugin.bot.plugins \
			or channel in plugin.bot.plugins["monitor"].module\
				.get_channels_by_con_and_nick( connection, nick )


def fun_amok( plugin, connection, channel, source_nick, victim ):
	if victim:
		if is_on_channel( plugin, connection, channel, victim ):
			txt = "kettet %(victim)s wie verlangt nongalant an die Heizungsrohe."
		else:
			txt = "sieht: %(source_nick)s kommt beim anketten etwas durcheinander und kettet sich selbst an die Heizung..."
	else:
		txt = "kettet %(source_nick)s an die Heizung."
	connection.action( channel, txt % locals() )


def fun_applause( plugin, connection, channel, source_nick, victim ):
	if is_on_channel( plugin, connection, channel, victim ):
		txt = "sieht: %(source_nick)s applaudiert %(victim)s."
	else:
		txt = "sieht: Das Publikum flippt förmlich aus."
	if random.randint(0,10)>6:
		txt += "  Stehende Ovationen! :D"
	connection.action( channel, txt % locals() )


def fun_assimilate( plugin, connection, channel, source_nick, victim ):
	if random.randint(0,10)>7:
		connection.privmsg( channel, "Resistance wasn't futile!" )
	else:
		if victim:
			if victim==source_nick:
				txt = "sees: %(source_nick)s, you can't assimilate yourself.  Think about it!"
			if victim==connection.get_nickname():
				txt = "gets assimilated by %(source_nick)s.  Watch out!"
			elif is_on_channel( plugin, connection, channel, victim ):
				txt = "sees: %(source_nick)s assimilates %(victim)s.  Resistance is futile!"
				if random.randint(0,10)>7:
					txt += "  YES, another cube filled!"
			else:
				txt = "sees: %(source_nick)s tries to assimilate %(victim)s ... not found.  Check your bionic implants."
		else:
			txt ="assimilates %(source_nick)s."
		connection.action( channel, txt % locals() )


def fun_blush( plugin, connection, channel, source_nick, victim ):
	what = [ \
		"%(source_nick)s errötet.",
		"%(source_nick)s guckt verschämt.",
		"%(source_nick)s wird rot wie ne Tomate.",
		"%(source_nick)s ist total süss, wenn verschämt!",
		"%(source_nick)s wird rot. Ein sehr kräftiges bis kaminrotes Rot-Rot.",
	]
	if victim==connection.get_nickname():
		txt = random.choice( what )
		source_nick = ""
	elif victim and victim!=source_nick \
			and is_on_channel( plugin, connection, channel, victim ):
		txt = "sieht: %(source_nick)s bringt %(victim)s zum erröten."
	else:
		txt = "sieht: "+random.choice( what )
	connection.action( channel, txt % locals() )


def fun_bow( plugin, connection, channel, source_nick, victim ):
	connection.action( channel, "hält ein Schild hoch, mit der Aufschrift: \"beta\"" )


def fun_cry( plugin, connection, channel, source_nick, victim ):
	connection.action( channel, "geht in Deckung. Feuchtigkeit ist nicht gut für offenliegende Schaltkreise." )


def fun_damn( plugin, connection, channel, source_nick, victim ):
	connection.action( channel, "liest vom Zettel ab: \"IOError: [Errno 2] No such file or directory: 'damn'\" und kratzt sich am Elektronenhirn" )


def fun_fast( plugin, connection, channel, source_nick, victim ):
	connection.action( channel, "ist FAST...  fertig." )


HARTEI_LINES = []
def fun_hartei( plugin, connection, channel, source_nick, victim ):
	global HARTEI_LINES
	if not HARTEI_LINES:
		HARTEI_LINES = load_lines_from_file( "harteier.txt" )
	if victim:
		if victim==connection.get_nickname() and random.randint(0,10)>4:
			txt = "grinst blöd und hält dich fürn glatten"
		elif is_on_channel( plugin, connection, channel, victim ):
			txt = "sieht: %(source_nick)s nennt %(victim)s nen"
		else:
			txt = "sieht: %(source_nick)s hats richtig derbe versemmlt, ist wohl ein"
	else:
		txt = "betitelt %(source_nick)s als"
	synonym = random.choice( HARTEI_LINES )
	txt = txt % locals()+" "+synonym
	connection.action( channel, txt )


def fun_hossa( plugin, connection, channel, source_nick, victim ):
	connection.action( channel, "fragt: Hoppla?" )


def fun_hug( plugin, connection, channel, source_nick, victim ):
	howtos = ["umarmt", "knuddelt", "streichelt", "hätschelt"]
	howto = random.choice( howtos )
	success = True
	if source_nick==victim:
		txt = "sieht, dass %(source_nick)s sich selbst ganz doll lieb hat."
		success = False
	elif not victim:
		txt = "%(howto)s %(source_nick)s"
	elif not is_on_channel( plugin, connection, channel, victim ):
		txt = "stellt fest, dass das nich möglich ist, weil %(victim)s nicht hier ist."
		success = False
	else:
		txt = "sieht: %(source_nick)s %(howto)s %(victim)s"
	# no success :)
	if success and random.randint(0,10)>7 and victim:
		fails = [ \
			"%(source_nick)s stolpert beim Versuch %(victim)s zu umarmen. %(source_nick)ss Lippen berühren die Füße ... %(source_nick)s KÜSST förmlich %(victim)ss Füße!",
			"%(source_nick)s schaut zu %(victim)s, öffnet die Arme und läuft... ins Leere. Vielleicht brauchst du eine neue Brille?",
			"%(source_nick)s eilt mit geöffneten Armen zu %(victim)s, stößt sich den Kopf am Kronleuchter *boing* ... und träumt nun süß von %(victim)s.",
			"%(source_nick)s %(howto)s %(victim)s, öffnet die Augen und sieht:  Es ist %(victim)ss Papa!",
			"%(source_nick)s %(howto)s %(victim)s, öffnet die Augen und sieht:  Es ist %(victim)ss Mama!",
			"%(source_nick)s %(howto)s %(victim)s, öffnet die Augen und sieht:  Es ist %(victim)ss Schatz!",
			"%(source_nick)s %(howto)s %(victim)s, doch HALT: Was ist das in meinem Nacken?  %(source_nick)s öffnet die Augen und erkennt:  Es ist ein VAMPIR! *Schock*",
			"%(source_nick)s %(howto)s %(victim)s, doch HALT: Was ist das in meinem Nacken?  %(source_nick)s öffnet die Augen und erkennt:  Es ist ein BORG! *assimiliert werd*",
		]
		txt = "sieht: "+random.choice(fails)
		success = False
	if success:
		if random.randint(0,10)>7:
			txt += " "+random.choice( ["herzlich", "zärtlich", "leidenschaftlich"] )
		txt += "."
	connection.action( channel, txt % locals() )


def fun_kiss( plugin, connection, channel, source_nick, victim ):
	connection.action( channel, "geht in Deckung. Feuchtigkeit ist nicht gut für offenliegende Schaltkreise." )


# generische Servicefunktion verschiedene Zitatwidergabefunktionen
def load_lines_from_file( file_name ):
	lines = []
	try:
		f = open( "fundata/%s" % (file_name), "r" )
	except Exception as e:
		lines.append( str(e) ) # joke ;)
		return lines
	for line in f:
		if line and line[0]!="#" and line.split():
			lines.append( line.strip() )
	return lines


KLO_LINES = []
def fun_klo( plugin, connection, channel, source_nick, victim ):
	global KLO_LINES
	if not KLO_LINES:
		KLO_LINES = load_lines_from_file( "klo.txt" )
	if victim and victim!=source_nick:
		if victim==connection.get_nickname():
			txt = "sagt: Ich muss nicht auf's Klo, aber wenn du gehst:"
		elif is_on_channel( plugin, connection, channel, victim ):
			txt = "sieht: %(source_nick)s ruft %(victim)s hinterher:"
		else:
			txt = "fragt sich woher %(source_nick)s weiß, dass %(victim)s auf dem Klo ist."
			connection.action( channel, txt % locals() )
			return
	else:
		txt = "ruft %(source_nick)s hinterher:"
	txt += " "+random.choice( KLO_LINES )
	connection.action( channel, txt % locals() )		


def fun_miss( plugin, connection, channel, source_nick, victim ):
	connection.action( channel, "hat das ungute Gefühl, etwas wichtiges vergessenn zu haben..." )


orders = {}
def fun_order( plugin, connection, channel, source_nick, drink ):
	global orders
	if (connection,channel) in orders:
		connection.action( channel, "machts garnix, solang die alte Bestellung nicht raus ist :P." )
		return
	txt = "schmeißt ne Runde"
	if not drink:
		drinks = [ "coffee", "vodka", "beer", "coke", "water", "lemon juice",
			"tea", "arabian coffee", "fresh air", "bot oil", "Cuba Libre",
			"Strawberry Magherita", "ACID", "Ambrosia", "Banana Milk Shake",
			"Bloody Mary", "the usual", "nectar" ]
		drink = random.choice( drinks )
	else:
		txt = "wird wachgeklingelt: %(source_nick)s "+txt
		if random.randint(0,10)>6:
			drink = "gesegnets "+drink
		if random.randint(0,10)>7:
			drink += " (+%d)" % (random.randint(0,5))
	txt += " "+drink
	connection.action( channel, txt % locals() )
	timer = Timer( 5+random.randint(0,10), serve_order, 
		(plugin,connection,channel,drink) )
	orders[(connection,channel)] = timer
	plugin.timers.append( timer )
def serve_order( plugin, connection, channel, drink ):
	global orders
	del orders[(connection,channel)]
	waiter = "waiter"
	if random.randint(0,10)>4:
		waiter = "Fräuleinmann"
	if random.randint(0,10)>8:
		txt = "sieht: Das %(waiter)s kommt endlich und verschüttet unachtsamerweise die Hälfe des %(drink)s."
	else:
		txt = "sieht: Das %(waiter)s kommt und serviert %(drink)s."
	connection.action( channel, txt % locals() )


PHRASE_LINES = []
def fun_phrase( plugin, connection, channel, source_nick, victim ):
	global PHRASE_LINES
	if not PHRASE_LINES:
		PHRASE_LINES = load_lines_from_file( "phrases.txt" )
	connection.action( channel, "sagt: " + random.choice(PHRASE_LINES) )


def fun_relax( plugin, connection, channel, source_nick, victim ):
	connection.action( channel, "vernimmt die Worte und harrt stoisch der Dinge, die da kommen mögen..." )


def fun_roll( plugin, connection, channel, source_nick, victim ):
	if random.randint(0,20)>2:
		a = random.randint(1,6)
		b = random.randint(1,6)
		_sum = a + b
		connection.action( channel, "lässt die Würfel für %(source_nick)s sprechen (2d6): %(a)d und %(b)d = %(_sum)d" % locals() )
	elif random.randint(0,3)>1:
		connection.action( channel, "*lol*  Jaja... roll du nur mal..." )
	else:
		connection.action( channel, "hat auch irgendwie Lust auf frische Brötchen." )

def fun_smoke( plugin, connection, channel, source_nick, victim ):
	connection.action( channel, "lässt das diodenbeleuchtete Nichtraucherschild aufleuchten und schaut grimmig." )


def fun_steal( plugin, connection, channel, source_nick, victim ):
	connection.action( channel, "geht in Deckung. Langfinger sind nicht gut für offenliegende Schaltkreise." )


def fun_strike( plugin, connection, channel, source_nick, victim ):
	connection.action( channel, "hat keine Angst vor Terroristen." )


def fun_seen( plugin, connection, channel, source_nick, victim ):
	if not victim:
		victim = source_nick
	connection.action( channel, "findet, dass es in Mecklenburg-Vorpommern schöne Seen gibt, weiß aber nicht was %(victim)s davon hält." % locals() )


WEICHEI_LINES = []
def fun_weichei( plugin, connection, channel, source_nick, victim ):
	global WEICHEI_LINES
	if not WEICHEI_LINES:
		WEICHEI_LINES = load_lines_from_file( "weicheier.txt" )
	if victim:
		if victim==connection.get_nickname() and random.randint(0,10)>4:
			txt = "lächelt mild und hält dich fürn"
		elif is_on_channel( plugin, connection, channel, victim ):
			txt = "sieht: %(source_nick)s nennt %(victim)s nen"
		else:
			txt = "sieht: %(source_nick)s hats vergurkt, ist wohl ein"
	else:
		txt = "nennt %(source_nick)s nen"
	synonym = random.choice( WEICHEI_LINES )
	txt = txt % locals()+" "+synonym
	connection.action( channel, txt )


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
			if "fun_"+command in globals() and approve_action():
				globals()["fun_"+command]( plugin, connection, channel, source_nick, cargs )


HANDLERS = {
	"privmsg" : handle_event,
	"pubmsg" : handle_event
}

