#!/usr/bin/python3

from bot import Bot

bot = None
def main():
	global bot
	bot = Bot( "irc.freenode.net", "mydemobot" )
	bot.load_plugin( "debug" ) # FIXME
	bot.load_plugin( "monitor" )
	#bot.load_plugin( "nickserv" )
	#nickserv = bot.plugins["nickserv"].module
	#nickserv.NICKSERV_ACCOUNTS[ ("irc.freenode.net","NickServ!NickServ@services.freenode.net") ] \
	#	= ("mydemobot","74cOpEtGN8")
	bot.join( '#mytestchannel' )
	bot.load_plugin( "quiz" )
	quiz = bot.plugins["quiz"].module 
	quiz.QUIZ_CHANNELS.append( "#mytestchannel" )
	quiz.reload_quizdata( ".*\.de" )
	bot.load_plugin( "fun" )
	bot.run()


if __name__ == "__main__":
	main()

