import time, re, random, os, os.path, imp

DEBUG = True

QUIZ_CHANNELS = []

EASY = 0
MEDIUM = 1
HARD = 2


last_action_time = 0
ACTION_TIMEOUT = 1.5

def approve_action( timeout=ACTION_TIMEOUT ):
	global last_action_time
	if last_action_time + timeout > time.time():
		return False
	else:
		last_action_time = time.time()
		return True


class Problem:
	def __init__( self, question=None, solutions=[], level=MEDIUM, url=None, 
					hint_count=5, author=None, tags=[], hints=[],
					comment=None, score=1, source=None ):
		self.question = question
		self.solutions = solutions
		self.level = level
		self.url = url
		self.hint_count = hint_count
		self.fix_hint_count()
		self.author = author
		self.tags = tags
		self.hints = hints
		self.comment = comment
		self.score = score
		self.source = source
	def fix_hint_count( self ):
		if self.solutions:
			self.hint_count = min( len(self.solutions[0]), self.hint_count )
	def check_answer( self, answer ):
		digraphs = {
			"ä" : "ae",
			"Ä" : "Ae",
			"ö" : "oe",
			"Ö" : "Oe",
			"ü" : "ue",
			"Ü" : "Ue",
			"ß" : "ss", #sz?
		}
		digraph_answer = answer
		for letter in digraphs:
			digraph_answer = digraph_answer.replace( letter, digraphs[letter] )
		for solution in self.solutions:
			for _answer in [answer,digraph_answer]:
				if( re.match(solution, _answer, re.IGNORECASE) ):
					return True
		return False


class Quiz:
	def __init__( self, connection, channel, problems, limit=30 ):
		self.connection = connection
		self.channel = channel
		self.current_timeout = 10
		self.next_action = time.time() + 2 # Schnell starten!
		self.problem_count_limit = limit
		self.problems = random.sample( problems, min(self.problem_count_limit,len(problems)) )
		self.problem_count = 0
		if self.problems:
			self.state = self.ask_question
		else:
			self.state = self.idle
		self.scores = {}
		self.last_score_request = 0
		self.termination_requests = {}
		self.skip_requests = {}
	def process_once( self ):
		if( time.time() > self.next_action ):
			self.real_process_once()
	def real_process_once ( self ):
		self.next_action = time.time() + self.current_timeout
		self.state()
	def ask_question( self ):
		problem = self.problems[self.problem_count]
		self.connection.privmsg( self.channel, "Frage %d von %d: %s (%s)" \
				% (self.problem_count+1, len(self.problems), 
					problem.question, 
					", ".join(problem.tags)) )
		self.last_action = time.time()
		self.state = self.show_hint
		self.current_hint = 0
	def show_hint( self ):
		problem = self.problems[self.problem_count]
		if( self.current_hint >= problem.hint_count ):
			self.show_solution()
			return
		hint = ""
		for i in range(len(problem.solutions[0])):
			if (i-self.current_hint)%problem.hint_count == 0:
				hint += problem.solutions[0][i]
			else:
				hint += '·'
		self.connection.privmsg( self.channel, hint )
		self.current_hint += 1
	def show_solution( self ):
		self.skip_requests = {}
		problem = self.problems[self.problem_count]
		self.connection.privmsg( self.channel, "Lösung: %s  (Quelle: %s%s)" \
			% (problem.solutions[0], 
				problem.source or "unbekannt", 
				problem.author and " von "+problem.author or "") )
		self.problem_count += 1
		if self.problem_count >= min( self.problem_count_limit,len(self.problems) ):
			self.state = self.show_ranking
			self.next_action = time.time() + 1 # Schnell Auswerten!
		else:
			self.state = self.ask_question
	def get_ranking( self ):
		ranking = []
		for player in self.scores:
			ranking.append( (self.scores[player], player) )
		ranking.sort( reverse=True ) # siehe auch add_score()
		return ranking
	def show_ranking( self ):
		if not self.state == self.show_ranking:
			if self.last_score_request > time.time()-self.current_timeout:
				return # DoS-Protection for user score requests
			self.last_score_request = time.time()
		ranking = self.get_ranking()
		# Rangliste nur zeigen, wenn auch wirklich jemand gespielt hat:
		if not ranking:
			self.connection.privmsg( self.channel, "Niemand hat mitgespielt :(" )
		elif ranking[0][0][0]==0:
			pass # keine Punkte -> kein Gewinner
		else:
			self.connection.privmsg( self.channel, "Rangliste:" )
			prev_points = points = None
			for i in range(1,len(ranking)+1):
				comment = ""
				if self.state == self.show_ranking and i==1:
					comment += " <== Gewinner nach %d von %d Fragen" % (self.problem_count, len(self.problems))
				time.sleep( 1 ) # FIXME: Queue-Manager!
				pair = ranking[i-1]
				player = pair[1]
				prev_points = points
				points = pair[0][0]
				if prev_points and prev_points==points:
					comment += " (später erreicht)"
				self.connection.privmsg( self.channel, "%(i)d. %(player)s: %(points)d Punkte%(comment)s" % locals() )
		# Nur am Quizende in den Ruhezustand gehen:
		if self.state == self.show_ranking:
			self.termination_requests = {}
			self.state = self.idle
	def idle( self ):
		pass
	def add_score( self, player, points=0 ):	
		if player not in self.scores:
			self.scores[ player ] = [0,0] # no item assignment on tuples 
		self.scores[ player ][0] += points
		# negativer Timestamp mit zweiten Tuple-Element führt bei 
		# Rückwärtssortierung dazu, dass Spieler, die einen bestimmten
		# Punktestand früher erreicht haben als andere, weiter vorn
		# in der Auswertung landen:
		self.scores[ player ][1] = -time.time()
	def get_score( self, player ):
		if player in self.scores:
			return self.scores[ player ][0]
		else:
			return 0
	def check_answer( self, player, answer ):
		if self.state == self.show_hint:
			problem = self.problems[self.problem_count]
			if problem.check_answer( answer ):
				self.add_score( player, int(problem.score) )
				score = None
				points = 0
				position = 0
				for score in self.get_ranking():
					position += 1
					if score[1] == player:
						points = score[0][0]
						break
				points = self.get_score( player )
				self.connection.privmsg( self.channel, "%(player)s hat gelöst!  Punktestand: %(points)d  (%(position)d. Platz)" % locals() )
				self.next_action = time.time() + 1 # Schnell Lösen!
				self.state = self.show_solution
	def check_termination_quorum( self, voter ):
		if self.state in [self.idle]:
			return False
		if voter not in self.scores or voter in self.termination_requests:
			return False # Flood protection
		self.termination_requests[ voter ] = True
		for player in self.scores:
			if player not in self.termination_requests:
				if len(self.termination_requests)==1:
					self.connection.privmsg( self.channel,
						"Um das Quiz abzubrechen, müssen %s dafür stimmen." \
							% (", ".join(self.scores.keys())) )
				return False
		return True
	def check_skip_quorum( self, voter ):
		self.skip_requests[ voter ] = True
		for player in self.scores:
			if player not in self.skip_requests:
				return False
		return True
	def vote_skip( self, voter ):
		if not self.state == self.show_hint:
			return
		if voter not in self.scores or voter in self.skip_requests:
			return # Flood protection
		if self.check_skip_quorum( voter ):
			self.connection.privmsg( self.channel, "Frage abgebrochen." )
			self.show_solution()
		elif len(self.skip_requests)==1:
			self.connection.privmsg( self.channel, 
				"Um die Frage abzubrechen, müssen %s dafür stimmen." \
					% (", ".join(self.scores.keys())) )


class MoxquizzReader:
	SCALARS = {
		"Question" : "question",
		"Author" : "author",
		"Level" : "level",
		"Comment" : "comment",
		"Score" : "score",
		"TipCylce" : "hint_count"
	}
	VECTORS = {
		"Category" : "tags",
		"Answer" : "solutions",
		"Regexp" : "solutions",
		"Tip" : "hints",
	}
	def __init__( self, file_path, problems ):
		infile = open( file_path, "r" )
		problem = None
		count = 0
		for line in infile:
			result = re.match( "^([a-zA-Z]+): (.*)$", line )
			if result:
				key = result.group(1)
				value = result.group(2)
				if not problem:
					problem = Problem()
					count += 1
					problem.source = "%s#%d" % (os.path.split(file_path)[-1], count)
					# FIXME: Wieso müssen die Listen hier explizit 
					# initialisiert, werden, damit getattr sie nicht 
					# vermischt?
					problem.solutions = []
					problem.tags = []
					problem.hints = []
				if key in MoxquizzReader.SCALARS:
					setattr( problem, MoxquizzReader.SCALARS[key], value )
				elif key in MoxquizzReader.VECTORS:
					getattr( problem, MoxquizzReader.VECTORS[key] ).append( value )
			elif problem and not line.split():
				self.store_problem( problem, problems )
				problem = None
		if problem:
			self.store_problem( problem, problems )
		infile.close()
	def store_problem( self, problem, problems ):
		self.fix_solutions( problem )
		problem.fix_hint_count()
		problems.append( problem )
	# Seltsame Einzelwortmarkierungen finden, entfernen und
	# Einzelwortmuster zur Lösungsliste hinzufügen:
	def fix_solutions( self, problem ):
		answer = problem.solutions[0]
		result = re.findall( '#([^#]+)#', answer )
		if result: 
			problem.solutions[0] = answer.replace('#', '')
			problem.solutions.append( result[0] )


PROBLEMS = []
import quizproblems
PROBLEMS += quizproblems.PROBLEMS

def load_quizdata( file_pattern, reload=False, list=False ):
	global PROBLEMS
	if not list:
		if reload:
			globals()["PROBLEMS"] = []
		if file_pattern == "internal":
			imp.reload( quizproblems )
			PROBLEMS += quizproblems.PROBLEMS
	datadir = "quizdata"
	files = []
	for file_name in os.listdir( datadir ):
		try:
			if re.match( file_pattern, file_name ):
				files.append( file_name )
		except Exception as e:
			print( str(load_quizdata)+" ("+file_pattern+"): "+str(e) )
			break
	if not list:
		for file_name in files:
			file_path = os.path.join( datadir, file_name )
			file_path = file_path.replace( "..", "" )
			MoxquizzReader( file_path, globals()["PROBLEMS"] )
	return files
		
def reload_quizdata( file_pattern ):
	load_quizdata( file_pattern, reload=True )


def find_problems_by_tags( filter_tags=[] ):
	global PROBLEMS
	filter_tags = [ lt for lt in map(lambda t: t.lower(), filter_tags) ]
	problems_by_tags = {}
	unique_problems = {}
	for problem in PROBLEMS:
		for tag in problem.tags:
			matched = not filter_tags
			for filter_tag in filter_tags:
				try:
					matched = re.findall( filter_tag, tag, re.IGNORECASE ) != []
				except Exception as e:
					print( str(find_problems_by_tags)+" ("+str(filter_tag)+"): "+str(e) )
					return problems_by_tags, [problem for problem in unique_problems.keys()]
				if matched:
					break
			if matched:
				if tag not in problems_by_tags.keys():
					problems_by_tags[ tag ] = []
				problems_by_tags[ tag ].append( problem )
				unique_problems[ problem ] = True
	return problems_by_tags, [problem for problem in unique_problems.keys()]

def print_help( plugin, connection, response_target ):
	connection.privmsg( response_target, "Quizbefehle: !ask [ANZAHL] [REGEX ...]: Quiz starten (mit ANZAHL Fragen und auf REGEX passenden Kategorien)," )
	connection.privmsg( response_target, "    !stop : Quiz anhalten, !revolt : Frage überspringen, !score : Punktezahl anzeigen," )
	connection.privmsg( response_target, "    !tags REGEX : auf REGEX passende Tags für !ask und Statistiken dazu anzeigen," )
	connection.privmsg( response_target, "    !quizdata reload REGEX : passende Quizfragen-Dateien neu laden," )
	connection.privmsg( response_target, "    !quizdata list REGEX : passende Quizfragen-Dateien auflisten," )
	print_problem_stats( plugin, connection, response_target )

def print_regex_help( plugin, connection, response_target ):
	connection.privmsg( response_target, 
		"Hinweis: Verwendeter Regex-Dialekt: http://docs.python.org/3.2/library/re.html#regular-expression-syntax" )

def print_problem_stats( plugin, connection, response_target ):
	global PROBLEMS
	connection.privmsg( response_target, "%d Fragen verfügbar." % len(PROBLEMS) )

quizzes_by_channel = {}

def handle_event( plugin, connection, event ):
	global PROBLEMS
	source = event.source()
	source_nick = source.split("!")[0]
	target = event.target()
	args = event.arguments()
	if target in QUIZ_CHANNELS:
		response_target = target
	elif target==connection.get_nickname():
		response_target = source_nick
	else:
		return # TODO: evtl. Hinweis auf Quiz-Channel geben
	quiz = None
	if response_target in quizzes_by_channel:
		quiz = quizzes_by_channel[ response_target ]
	if event.eventtype()=="join":
		if not quiz and approve_action( 10 ):
			print_help( plugin, connection, response_target )
		elif approve_action():
			connection.privmsg( response_target, "Hallo %s! Es läuft gerade ein Quiz. Rate einfach mit!" % source_nick )
			quiz.show_ranking()
		return
	command = re.match( "^!(\S+)", args[0] )
	cargs = re.findall( "\s+(\S+)", args[0] )
	if command:
		command = command.group(1)
	if command=="help" and approve_action( 10 ):
		print_help( plugin, connection, response_target )
	elif command in ["ask", "quiz"]:
		if not quiz or quiz.state == quiz.idle:
			limit = 30
			for carg in cargs:
				try:
					limit = int(carg)
					break # erste Zahl wird als Fragenlimit interpretiert
				except:
					pass
			tags, problems = find_problems_by_tags( cargs )
			quiz = Quiz( connection, response_target, problems, limit=limit )
			quiz.add_score( source_nick )
			quizzes_by_channel[ response_target ] = quiz
		else:
			pass
	elif command == "tags" and approve_action():
		probs_by_tags, probs = find_problems_by_tags( cargs )
		taglist = ", ".join( probs_by_tags.keys() )
		if len(taglist)>300:
			taglist = taglist[:297]+"..."
		connection.privmsg( response_target, 
			"Tags: %s (insgesamt %d mit %d Fragen)" \
			% (taglist, len(probs_by_tags), len(probs)) )
		if( len(probs)==0 ):
			print_regex_help( plugin, connection, response_target )
	elif quiz and command == "stop":
		if quiz.check_termination_quorum( source_nick ):
			quiz.state = quiz.show_ranking
			connection.privmsg( response_target, "Quiz abgebrochen." )
	elif quiz and command == "revolt":
		quiz.vote_skip( source_nick )
	elif quiz and command == "score" and approve_action():
		quiz.show_ranking()
	elif command == "quizdata" and approve_action():
		if cargs and cargs[0] == "clear":
			globals()["PROBLEMS"] = []
			connection.privmsg( response_target, "%d Fragen verfügbar." % len(PROBLEMS) )
		elif len(cargs) in [1,2] and cargs[0] in ("load","reload","list"):
			reload = (cargs[0] == "reload")
			list = (cargs[0] == "list")
			file_pattern = len(cargs)==2 and cargs[1] or ".*"
			files = []
			try:
				files = load_quizdata( file_pattern, reload=reload, list=list )
				msg = "Dateien: "+", ".join(files)
				if len(msg) > 400:
					msg = msg[:397]+"..."
				connection.privmsg( response_target, msg )
			except Exception as e:
				connection.privmsg( response_target, "Kann %s nicht laden: %s" % (file_pattern, str(e)) )
			if not list:
				print_problem_stats( plugin, connection, response_target )
			if not files:
				print_regex_help( plugin, connection, response_target )
	elif response_target in quizzes_by_channel:
		quizzes_by_channel[ response_target ].check_answer( source_nick, args[0] )
	elif approve_action( 10 ):
		print_help( plugin, connection, response_target )

def process_once( plugin ):
	for quiz in quizzes_by_channel.values():
		quiz.process_once()

HANDLERS = {
	"privmsg" : handle_event,
	"pubmsg" : handle_event,
	"join" : handle_event,
}

