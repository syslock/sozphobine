g_disabled_on_channels = [ '#sozphobie' ]

import random
import math
import time

class class_dict(object):
	pass

g_game_states = {}
g_game_state = None

def provide_state(event):
	global g_game_states
	global g_game_state

	channel = event.target()
	if channel in g_disabled_on_channels: return True

	if channel not in g_game_states:
		g_game_states[channel] = class_dict()
		g_game_state = g_game_states[channel]

		g_game_state.active  = None
		g_game_state.pot     = None
		g_game_state.einsatz = None
		g_game_state.cards   = None

		g_game_state.round     = None
		g_game_state.whos_turn = None

		g_game_state.players = None
		g_game_state.chips   = None
		g_game_state.folded  = None

		g_game_state.flop             = None
		g_game_state.gesetzt          = None
		g_game_state.last_time        = None
		g_game_state.round_3_showed   = None
	else:
		g_game_state = g_game_states[channel]
	
# picture_idx 0..8 => '2'..'10'; picture_idx 9..12 => 'B' 'D' 'K' 'A'
# color_idx 0..3 => Pik Kreuz Herz Karo
# das deck ist picture-major geschachtelt, d.h. deck mit indizes 0..51 startet 'Pik 2', 'Kreuz 2' etc

pic_2 = 0
pic_3 = 1
pic_4 = 2
pic_5 = 3
pic_6 = 4
pic_7 = 5
pic_8 = 6
pic_9 = 7
pic_10 = 8
pic_B = 9
pic_D = 10
pic_K = 11
pic_A = 12

def card_picture(card_idx):
	return math.floor(card_idx / 4)

def card_color(card_idx):
	return card_idx - card_picture(card_idx) * 4

def ueber(a,b):
	x = 1
	y = 1
	for i in range(b):
		x  *= a - i
		y  *= i + 1
	return x / y

# regeln siehe wikipedia

kombi_royal_flush    = ueber(1,1) * 4
kombi_straight_flush = ueber(9,1) * 4
kombi_vierling       = ueber(13,1) * ueber(48,1)
kombi_full_house     = ueber(13,1) * ueber(4,3) * ueber(12,1) * ueber(4,2)
kombi_flush          = ueber(13,5) * ueber(4,1) - 36 - 4
kombi_straight       = ueber(10,1) * pow(ueber(4,1), 5) - 36 - 4
kombi_drilling       = ueber(13,1) * ueber(4,3) * ueber(12,2) * pow(ueber(4,1), 2)
kombi_zwei_paare     = ueber(13,2) * pow(ueber(4,2), 2) * ueber(11,1) * ueber(4,1)
kombi_ein_paar       = ueber(13,1) * ueber(4,2) * ueber(12,3) * pow(ueber(4,1), 3)
kombi_alle           = ueber(52,5)

temp = kombi_alle

temp -= kombi_royal_flush   ; hand_royal_flush    = temp
temp -= kombi_straight_flush; hand_straight_flush = temp
temp -= kombi_vierling      ; hand_vierling       = temp
temp -= kombi_full_house    ; hand_full_house     = temp
temp -= kombi_flush         ; hand_flush          = temp
temp -= kombi_straight      ; hand_straight       = temp
temp -= kombi_drilling      ; hand_drilling       = temp
temp -= kombi_zwei_paare    ; hand_zwei_paare     = temp
temp -= kombi_ein_paar      ; hand_ein_paar       = temp

hand_high_card = 0

g_hand_names = {
hand_royal_flush   : 'Royal Flush',
hand_straight_flush: 'Straight Flush',
hand_vierling      : 'Vierling',
hand_full_house    : 'Full House',
hand_flush         : 'Flush',
hand_straight      : 'Straight',
hand_drilling      : 'Drilling',
hand_zwei_paare    : 'Zwei Paare',
hand_ein_paar      : 'Ein Paar',
hand_high_card     : 'High Card' }

def reset_colors():
	return ''

def underline():
	return '' + '10' # underline code ist in notepad unsichtbar

def esc_nick(nick):
	return nick[:1] + '' + nick[1:]

def rank_hand_names():
	rank_colors = [
	'7,8',
	'1,9',
	'0,13',
	'0,4',
	'0,14',
	'0,3',
	'0,12',
	'0,7',
	'0,14',
	'1,15' ]
	rank = 1
	for k, v in sorted(g_hand_names.items(), reverse=True):
		g_hand_names[k] = '15,2' + str(rank) + rank_colors[rank-1] + ' ' + g_hand_names[k] + ' 15,2' + str(rank) + reset_colors()
		rank += 1
rank_hand_names()

def plural(card):
	if card_picture(card) <= pic_10:
		return 'ern'
	elif card_picture(card) == pic_B:
		return 'uben'
	elif card_picture(card) == pic_D:
		return 'amen'
	elif card_picture(card) == pic_K:
		return 'önigen'
	elif card_picture(card) == pic_A:
		return 'ssen'

def hand_name(hand):
	for k, v in sorted(g_hand_names.items(), reverse=True):
		if hand >= k:
			return g_hand_names[k]

def colors_same(hand):
	return card_color(hand[0]) == card_color(hand[1])\
	and    card_color(hand[0]) == card_color(hand[2])\
	and    card_color(hand[0]) == card_color(hand[3])\
	and    card_color(hand[0]) == card_color(hand[4])

def pictures_same(hand):
	return card_picture(hand[0]) == card_picture(hand[1])\
	and    card_picture(hand[0]) == card_picture(hand[2])\
	and    card_picture(hand[0]) == card_picture(hand[3])\
	and    card_picture(hand[0]) == card_picture(hand[4])

def pictures_straight(hand): # todo: ace can play low (etvl auch übrige around-corner möglichkeiten)
	return card_picture(hand[0]) == card_picture(hand[1]) - 1\
	and    card_picture(hand[1]) == card_picture(hand[2]) - 1\
	and    card_picture(hand[2]) == card_picture(hand[3]) - 1\
	and    card_picture(hand[3]) == card_picture(hand[4]) - 1

g_pictures = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'B', 'D', 'K', 'A']

for i in range(9):
	g_pictures[i] = '0' + g_pictures[i]

# pik kreuz herz karo => mirc farben 3 4 7 12
g_colors = ['3,3', '4,4', '7,7', '12,12']

def card_name(card_idx):	
	name = g_colors[card_color(card_idx)]
	if card_picture(card_idx) != pic_10: name += '.'
	name += '0' + g_pictures[card_picture(card_idx)]
	return '' + name + '' + reset_colors()

def picture_name(card_idx):
	return g_pictures[card_picture(card_idx)]

# gibt möglichst homogenen rang von 0 wie mieseste Hand bis 2598959 wie beste (Royal Flush) zurück

def get_hand(cards): 
	cards = sorted(cards)

	# ROYAL FLUSH

	if colors_same(cards)\
	and pictures_straight(cards)\
	and card_picture(cards[0]) == pic_10:
		return hand_royal_flush + 3, 'Höchste Hand'

	# STRAIGHT FLUSH

	if colors_same(cards)\
	and pictures_straight(cards):
		return hand_straight_flush + card_picture(cards[0]) * ueber(4,1), 'mit ' + picture_name(cards[4]) + ' als höchster Karte'
		# todo: ace can play low, diesen wertebereich vor die anderen

	# VIERLING

	kicker = None

	# ungleiche karte ist drüber
	if  card_picture(cards[0]) == card_picture(cards[1])\
	and card_picture(cards[0]) == card_picture(cards[2])\
	and card_picture(cards[0]) == card_picture(cards[3]):
		kicker = cards[4]

	# ungleiche karte ist drunter
	if  card_picture(cards[1]) == card_picture(cards[2])\
	and card_picture(cards[1]) == card_picture(cards[3])\
	and card_picture(cards[1]) == card_picture(cards[4]):
		kicker = cards[0]
	
	if kicker != None:
		vierling = cards[1]
		return hand_vierling + card_picture(vierling) * ueber(48,1) + kicker\
		, 'aus ' + picture_name(vierling) + plural(vierling) + ' mit Kicker ' + picture_name(kicker) 

	# FULL HOUSE

	if  card_picture(cards[0]) == card_picture(cards[1])\
	and card_picture(cards[2]) == card_picture(cards[3])\
	and card_picture(cards[2]) == card_picture(cards[4])\
	\
	or  card_picture(cards[0]) == card_picture(cards[1])\
	and card_picture(cards[0]) == card_picture(cards[2])\
	and card_picture(cards[3]) == card_picture(cards[4]):

		drilling = cards[2]
		
		if card_picture(cards[0]) == card_picture(cards[2]):
			paar = cards[3] # rechts
		else:
			paar = cards[0] # links
		
		# drilling-major, da höherer drilling vor höherem paar gewinnt		

		return hand_full_house + card_picture(drilling) * ueber(4,3) * ueber(12,1) * ueber(4,2)\
		+ card_picture(paar) * ueber(4,2),\
		'mit ' + picture_name(drilling) + plural(drilling) + ' als Drilling und '\
		+ picture_name(paar) + plural(paar) + ' als Paar'
		
	# FLUSH

	if colors_same(cards):
		temp = 0
		text = 'aus den Karten'
		for i in range(5):
			# schliesst flushes mit ein, deshalb danach korrektur
			temp += card_picture(cards[4-i]) / (5-i) * ueber(12-i, 4-i)
			text += ' ' + picture_name(cards[4-i])
		alle = ueber(13, 5)
		temp *= (alle - kombi_royal_flush - kombi_straight_flush) / alle
		return hand_flush + temp, text

	# STRAIGHT

	if pictures_straight(cards):
		# schliesst flushes mit ein, deshalb danach korrektur
		kombi = pow(ueber(4,1), 5)
		temp = card_picture(cards[0]) * kombi
		alle = ueber(10,1) * kombi
		temp *= (alle - kombi_royal_flush - kombi_straight_flush) / alle
		return hand_straight + temp, 'mit ' + picture_name(cards[4]) + ' als höchster Karte'
		# todo: ace can play low

	# DRILLING

	drilling_idx = None

	for i in range(3):
		if  card_picture(cards[i]) == card_picture(cards[i+1])\
		and card_picture(cards[i]) == card_picture(cards[i+2]):
			drilling_idx = i
			break

	if drilling_idx != None:
		drilling = cards[2]

		kickers = []
		for i in range(5):
			if i != drilling_idx\
			and i != drilling_idx + 1\
			and i != drilling_idx + 2:
				kickers.append(cards[i])

		ret = hand_drilling + card_picture(drilling) * ueber(4,3) * ueber(12,2) * pow(ueber(4,1), 2)

		karten_rest = 48
		plaetze_rest = 1
		text = 'aus ' + picture_name(drilling) + plural(drilling) + ' mit den Kickern'
		for kicker in reversed(kickers):
			ret += card_picture(kicker) * ueber(karten_rest, plaetze_rest)
			karten_rest -= 1
			plaetze_rest -= 1
			text += ' ' + picture_name(kicker)

		return ret, text

	# ZWEI PAARE
	# da sortiert, kann restkarte c nur vor a, nach a oder nach b sein

	kicker = None

	# caabb
	if  card_picture(cards[1]) == card_picture(cards[2])\
	and card_picture(cards[3]) == card_picture(cards[4]):
		kicker = cards[0]

	# aacbb
	if  card_picture(cards[0]) == card_picture(cards[1])\
	and card_picture(cards[3]) == card_picture(cards[4]):
		kicker = cards[2]

	# aabbc
	if card_picture(cards[0]) == card_picture(cards[1])\
	and card_picture(cards[2]) == card_picture(cards[3]):
		kicker = cards[4]

	if kicker != None:
		low_pair  = cards[1]
		high_pair = cards[3]
		
		kicker_kombis = ueber(11,1) * ueber(4,1)
		
		# high_pair-major, weil höheres paar gewinnt
		return hand_zwei_paare\
		+ card_picture(high_pair) / 2 * ueber(12,1) * pow(ueber(4,2), 2) * kicker_kombis\
		+ card_picture(low_pair) / 2 * ueber(4,2) * kicker_kombis\
		+ kicker\
		, 'mit ' + picture_name(high_pair) + plural(high_pair) + ' als hohes Paar und '\
		+ picture_name(low_pair) + plural(low_pair) + ' als niedriges Paar und Kicker ' + picture_name(kicker)

	# EIN PAAR

	paar_idx = None
	for i in range(4):
		if  card_picture(cards[i]) == card_picture(cards[i+1]):
			paar_idx = i
			break

	if paar_idx != None:
		paar = cards[paar_idx]

		kickers = []
		# gone_kickers = 1
		# wegen einem paar ist eine kickermöglichkeit weg?
		# der kicker muss ja ungleich dem paar sein, sonst wärs nen drilling oder mehr
		for i in range(5):
			if i != paar_idx\
			and i != paar_idx + 1:
				# kickers.append(card_picture(cards[i]) * (13-gone_kickers)/13)
				kickers.append(cards[i])
				# gone_kickers += 1
				# und/oder muss man eigtl für die kicker auch durch ne anzahl von permutationen teilen?

		karten_rest = 11
		plaetze_rest = 2
		temp = 0
		text = 'aus ' + picture_name(paar) + plural(paar) + ' mit den Kickern'
		for kicker in reversed(kickers):
			temp += card_picture(kicker) * ueber(karten_rest, plaetze_rest)
			karten_rest -= 1
			plaetze_rest -= 1
			text += ' ' + picture_name(kicker)

		farben = pow(ueber(4,1), 3)
		return hand_ein_paar + card_picture(paar) * ueber(4,2) * ueber(12,3) * farben + temp * farben, text

	# HIGH CARD

	ret = hand_high_card
	text = 'mit den Karten'
	for i in range(5):
		card = cards[4-i]

		# billiger trick, resultat funzt damit für comparison, endet aber natürlich nicht bei hand_ein_paar wie gewünscht
		# richtiger wäre sowas wie: /  (5 - i) * ueber(4,1) * ueber(51-i, 4-i), aber das hat nen denkfehler drin
		ret += card_picture(card) * (5-i)

		text += ' ' + picture_name(card)

	# ret *= hand_ein_paar / kombi_alle, wäre evtl für mathematisch korrekten algo
	return ret, text

# die rang algos sind wahrscheinlich/leider mathematisch inkorrekt,
# lassen aber die notwendigen hand/kicker-vergleiche zu

def mk(a,b):
	return a*4+b

assert hand_royal_flush    <= get_hand( [ mk(pic_10, 3), mk(pic_B , 3), mk(pic_D, 3), mk(pic_K, 3), mk(pic_A, 3) ] )[0]
assert hand_straight_flush <= get_hand( [ mk(pic_9 , 3), mk(pic_10, 3), mk(pic_B, 3), mk(pic_D, 3), mk(pic_K, 3) ] )[0]
assert hand_vierling       <= get_hand( [ mk(pic_A , 0), mk(pic_A , 1), mk(pic_A, 2), mk(pic_A, 3), mk(pic_K, 3) ] )[0]
assert hand_full_house     <= get_hand( [ mk(pic_K , 2), mk(pic_K , 3), mk(pic_A, 1), mk(pic_A, 2), mk(pic_A, 3) ] )[0]
assert hand_flush          <= get_hand( [ mk(pic_9 , 3), mk(pic_B , 3), mk(pic_D, 3), mk(pic_K, 3), mk(pic_A, 3) ] )[0]
assert hand_straight       <= get_hand( [ mk(pic_10, 2), mk(pic_B , 3), mk(pic_D, 3), mk(pic_K, 3), mk(pic_A, 3) ] )[0]
assert hand_drilling       <= get_hand( [ mk(pic_D , 3), mk(pic_K , 3), mk(pic_A, 1), mk(pic_A, 2), mk(pic_A, 3) ] )[0]
assert hand_zwei_paare     <= get_hand( [ mk(pic_D , 3), mk(pic_K , 2), mk(pic_K, 3), mk(pic_A, 2), mk(pic_A, 3) ] )[0]
assert hand_ein_paar       <= get_hand( [ mk(pic_B , 3), mk(pic_D , 3), mk(pic_K, 3), mk(pic_A, 2), mk(pic_A, 3) ] )[0]
assert hand_high_card      <= get_hand( [ mk(pic_9 , 2), mk(pic_B , 3), mk(pic_D, 3), mk(pic_K, 3), mk(pic_A, 3) ] )[0]

assert hand_royal_flush    > get_hand( [ mk(pic_9 , 3), mk(pic_10, 3), mk(pic_B, 3), mk(pic_D, 3), mk(pic_K, 3) ] )[0]
assert hand_straight_flush > get_hand( [ mk(pic_A , 0), mk(pic_A , 1), mk(pic_A, 2), mk(pic_A, 3), mk(pic_K, 3) ] )[0]
assert hand_vierling       > get_hand( [ mk(pic_K , 2), mk(pic_K , 3), mk(pic_A, 1), mk(pic_A, 2), mk(pic_A, 3) ] )[0]
assert hand_full_house     > get_hand( [ mk(pic_9 , 3), mk(pic_B , 3), mk(pic_D, 3), mk(pic_K, 3), mk(pic_A, 3) ] )[0]
assert hand_flush          > get_hand( [ mk(pic_10, 2), mk(pic_B , 3), mk(pic_D, 3), mk(pic_K, 3), mk(pic_A, 3) ] )[0]
assert hand_straight       > get_hand( [ mk(pic_D , 3), mk(pic_K , 3), mk(pic_A, 1), mk(pic_A, 2), mk(pic_A, 3) ] )[0]
assert hand_drilling       > get_hand( [ mk(pic_D , 3), mk(pic_K , 2), mk(pic_K, 3), mk(pic_A, 2), mk(pic_A, 3) ] )[0]
assert hand_zwei_paare     > get_hand( [ mk(pic_B , 3), mk(pic_D , 3), mk(pic_K, 3), mk(pic_A, 2), mk(pic_A, 3) ] )[0]
assert hand_ein_paar       > get_hand( [ mk(pic_9 , 2), mk(pic_B , 3), mk(pic_D, 3), mk(pic_K, 3), mk(pic_A, 3) ] )[0]

def reset_deck():
	global g_game_state
	g_game_state.deck = []
	for i in range(52):
		g_game_state.deck.append(i)
	random.seed()
	for i in range(300):
		pos1 = random.randint(0, 51)
		pos2 = random.randint(0, 51)
		temp = g_game_state.deck[pos1]
		g_game_state.deck[pos1] = g_game_state.deck[pos2]
		g_game_state.deck[pos2] = temp

def take_card():
	global g_game_state
	card = g_game_state.deck[-1]
	g_game_state.deck = g_game_state.deck[:-1]
	return card

def group(number):
    s = '%d' % number
    groups = []
    while s and s[-1].isdigit():
        groups.append(s[-3:])
        s = s[:-3]
    return s + '.'.join(reversed(groups))

def cards_desc(cards):
	if cards == None: return ''
	cards = sorted(cards)
	text = ''
	for card in cards:
		if text != '': text += ' '
		text += card_name(card)
	#if len(cards) == 5:
	#	hand, high_cards = get_hand(cards)
	#	text += ' => ' + hand_name(hand) + ' ' + high_cards + ' => Rang ' + group(kombi_alle - hand)
	return text

				# cards = [ mk(pic_10, 3), mk(pic_B , 3), mk(pic_D, 3), mk(pic_K, 3), mk(pic_A, 3) ]
				# cards = [ mk(pic_9 , 3), mk(pic_10, 3), mk(pic_B, 3), mk(pic_D, 3), mk(pic_K, 3) ]
				# cards = [ mk(pic_A , 0), mk(pic_A , 1), mk(pic_A, 2), mk(pic_A, 3), mk(pic_K, 3) ]
				# cards = [ mk(pic_K , 2), mk(pic_K , 3), mk(pic_A, 1), mk(pic_A, 2), mk(pic_A, 3) ]
				# cards = [ mk(pic_9 , 3), mk(pic_B , 3), mk(pic_D, 3), mk(pic_K, 3), mk(pic_A, 3) ]
				# cards = [ mk(pic_10, 2), mk(pic_B , 3), mk(pic_D, 3), mk(pic_K, 3), mk(pic_A, 3) ]
				# cards = [ mk(pic_D , 3), mk(pic_K , 3), mk(pic_A, 1), mk(pic_A, 2), mk(pic_A, 3) ]
				# cards = [ mk(pic_D , 3), mk(pic_K , 2), mk(pic_K, 3), mk(pic_A, 2), mk(pic_A, 3) ]
				# cards = [ mk(pic_B , 3), mk(pic_D , 3), mk(pic_K, 3), mk(pic_A, 2), mk(pic_A, 3) ]
				# cards = [ mk(pic_9 , 2), mk(pic_B , 3), mk(pic_D, 3), mk(pic_K, 3), mk(pic_A, 3) ]

def colored(text):
	return '13' + text + reset_colors()

'''
kombis = {}

for a1 in range(7):
 for a2 in range(7):
  for a3 in range(7):
   for a4 in range(7):
    for a5 in range(7):
     c = [0,0,0,0,0,0,0]
     c[a1] += 1
     c[a2] += 1
     c[a3] += 1
     c[a4] += 1
     c[a5] += 1
     if  c[a1] <= 1\
     and c[a2] <= 1\
     and c[a3] <= 1\
     and c[a4] <= 1\
     and c[a5] <= 1:
      q = [a1,a2,a3,a4,a5]
      q = sorted(q)
      s = '['
      for i in range(5):
       s += str(q[i])
       if i < 4: s += ','
      s += ']'
      kombis[s] = True

for k, v in sorted(kombis.items()):
 print(k + ',')

assert len(kombis) == ueber(7,5)
'''

g_seven_kombis = [
[0,1,2,3,4],
[0,1,2,3,5],
[0,1,2,3,6],
[0,1,2,4,5],
[0,1,2,4,6],
[0,1,2,5,6],
[0,1,3,4,5],
[0,1,3,4,6],
[0,1,3,5,6],
[0,1,4,5,6],
[0,2,3,4,5],
[0,2,3,4,6],
[0,2,3,5,6],
[0,2,4,5,6],
[0,3,4,5,6],
[1,2,3,4,5],
[1,2,3,4,6],
[1,2,3,5,6],
[1,2,4,5,6],
[1,3,4,5,6],
[2,3,4,5,6] ]

def check_seven(seven_cards):
	highest = -1
	highest_desc = None
	for kombi in g_seven_kombis:
		cards = []
		for i in range(5):
			cards.append(seven_cards[kombi[i]])
		hand, desc = get_hand(cards)
		if hand > highest:
			highest = hand
			highest_desc = desc
	return highest, highest_desc

g_x_users_log = {}
g_x_users_log_time = {}

def pubmsg(plugin, connection, event):
	global g_game_state
	if provide_state(event): return

	channel = event.target()
	nick = event.source().split('!')[0]
	irc_text = event.arguments()[0]

	def say(text):
		try: # wegen unicode
			connection.privmsg(channel, text)
		except Exception as e:
			pass

	help = {
	'!poker': 'Poker neu starten',
	'join': 'Mitspielen',
	'ask': 'Runde beginnen oder weitermachen',
	'part': 'Nicht mehr mitspielen',
	'take': 'Idler zum call zwingen',
	'check': 'Nichts setzen',
	'call': 'Mitgehen',
	'raise': 'Prozentual erhöhen',
	'fold': 'Aus Runde aussteigen',
	'rank': 'Rangliste anzeigen' }

	def x_users_say(x, command):
		global g_x_users_log
		global g_x_users_log_time

		user = event.source()

		g_x_users_log     [user] = irc_text
		g_x_users_log_time[user] = time.time()

		wanters = []

		for k, v in g_x_users_log.items():
			if  g_x_users_log     [k] == command\
			and g_x_users_log_time[k] > time.time() - 20:
				wanters.append(k)

		if irc_text == command:
			if len(wanters) < x:
				say('Für "' + help[command] + '" müssen noch ' + str(x - len(wanters)) + ' weitere User ' + command + ' schreiben')
				return False
			else:
				for wanter in wanters:
					del(g_x_users_log     [wanter])
					del(g_x_users_log_time[wanter])
				return True

		return False

	def notice(nick, text):
		try: # wegen unicode
			connection.notice(nick, text)
		except Exception as e:
			pass

	def pot_desc():
		return 'Im Pot sind ' + str(g_game_state.pot) + ' Chips.'

	def skip_foldeds():
		while g_game_state.whos_turn < len(g_game_state.players):
			if g_game_state.players[g_game_state.whos_turn] not in g_game_state.folded: break
			g_game_state.whos_turn += 1

	def rank():
		if len(g_game_state.players) == 0:
			say('Es spielt niemand')
			return

		text = ''
		more_leaders = False
		iter = 0
		for player in sorted(g_game_state.chips, key=g_game_state.chips.get, reverse=True):
			if iter > 0 and g_game_state.chips[player] == first_score:
				text += ' und '
				more_leaders = True
			elif iter > 0:
				text += ' | '

			if g_game_state.chips[player] > 0:
				chips = str(g_game_state.chips[player])
			else:
				chips = 'out'
			text += player + ' (' + chips + ')'
			if iter == 0: first_score = g_game_state.chips[player]
			iter += 1

		if more_leaders:
			text = 'Es führen ' + text
		else:
			text = 'Es führt ' + text

		say(text)

	def reset_round():
		g_game_state.round = None
		g_game_state.whos_turn = None

		to_remove = []
		for player in g_game_state.players:
			if g_game_state.chips[player] <= 0:
				to_remove.append(player)

		for player in to_remove:
			g_game_state.players.remove(player)
			g_game_state.cards[player] = None

		g_game_state.players = g_game_state.players[1:] + g_game_state.players[:1]

		rank()

	def show_flop(ask_for_action):
		for player in g_game_state.players:

			if ask_for_action:
				text = colored(esc_nick(g_game_state.players[g_game_state.whos_turn])) + reset_colors() + '1 ist dran | '
			else:
				text = ''

			if player in g_game_state.folded:
				folded_desc = '14,15folded' + reset_colors()
			else:
				folded_desc = cards_desc(g_game_state.cards[player])

			text += 'Runde ' + str(1 + g_game_state.round) + ' | ' + player + ' ' + str(g_game_state.chips[player])\
			+ ' ' + folded_desc + ' 1| Pot ' + str(g_game_state.pot)\
			+ ' <- ' + str(g_game_state.einsatz)

			if g_game_state.flop != None: text += ' ' + cards_desc(g_game_state.flop)
					
			notice(player, text)

		if g_game_state.round == 3: g_game_state.round_3_showed

	def give_cards(player):
		g_game_state.cards[player] = []
		cards = g_game_state.cards[player]
		cards.append(take_card())
		cards.append(take_card())

	def iter_ask():
		g_game_state.last_time = time.time()

		if g_game_state.round == None:
			g_game_state.pot = 0
			g_game_state.einsatz = 10
			g_game_state.cards = {}
			g_game_state.folded = {}
			g_game_state.round = 0
			g_game_state.whos_turn = None
			g_game_state.flop = None
			g_game_state.round_3_showed = False

		if g_game_state.round == 0:
			if g_game_state.whos_turn == None:
				reset_deck()
				for player in g_game_state.players:
					give_cards(player)

				g_game_state.gesetzt = False
				g_game_state.whos_turn = 0
				skip_foldeds()

		elif g_game_state.round == 1:
			if g_game_state.whos_turn == None:
				g_game_state.flop = []
				for i in range(3):
					g_game_state.flop.append(take_card())

				g_game_state.gesetzt = False
				g_game_state.whos_turn = 0
				skip_foldeds()

		elif g_game_state.round == 2:
			if g_game_state.whos_turn == None:
				g_game_state.flop.append(take_card())

				g_game_state.gesetzt = False
				g_game_state.whos_turn = 0
				skip_foldeds()

		elif g_game_state.round == 3:
			if g_game_state.whos_turn == None:
				g_game_state.flop.append(take_card())

				g_game_state.gesetzt = False
				g_game_state.whos_turn = 0
				skip_foldeds()

		elif g_game_state.round == 4:
			highest = -1
			highest_desc = None
			winners = []
			for player in g_game_state.players:
				if player not in g_game_state.folded:
					hand, desc = check_seven(g_game_state.cards[player] + g_game_state.flop)
					if hand > highest:
						highest = hand
						highest_desc = desc
						winners = [player]
					elif hand == highest:
						winners.append(player)
			
			split = int(g_game_state.pot / len(winners))
			
			for winner in winners:
				g_game_state.chips[winner] += split

			text = str(g_game_state.pot) + ' Chips '

			if len(winners) > 1:
				text += 'gewinnen '
			else:
				text += 'gewinnt '

			farbig = '8,4'
			text += farbig

			iter = 0
			for winner in winners:				
				text += esc_nick(winner) + reset_colors() + ' mit ' + cards_desc(g_game_state.cards[winner])
				if iter < len(winners) - 1:
					text += ' und ' + farbig
				iter += 1

			text += reset_colors() + ' also '
			if len(winners) > 1: text += 'jeweils '

			text += hand_name(highest) + ' ' + highest_desc

			if len(winners) > 1:
				text += '. Jeder bekommt ' + str(split) + ' Chips'

			say(text)
			reset_round()
			return

		if g_game_state.round < 4:
			player = g_game_state.players[g_game_state.whos_turn]

			if g_game_state.chips[player] <= 0:
				next_turn()
				if g_game_state.round == 4 and not g_game_state.round_3_showed:
					show_flop(False)
				return True
			else:
				show_flop(True)
	
	def loop_ask():
		while iter_ask(): None

	def join():
		if nick in g_game_state.players:
			say(esc_nick(nick) + ': Du spielst bereits mit')
			return False

		#if g_game_state.round != None:
		#	say(esc_nick(nick) + ': Bitte zu Beginn der nächsten Runde einsteigen.')
		#	return False
		
		lowest_chips = None
		for player in g_game_state.players:
			if lowest_chips == None or g_game_state.chips[player] < lowest_chips:
				lowest_chips = g_game_state.chips[player]
		if lowest_chips == None or lowest_chips < 500: lowest_chips = 500

		pos = len(g_game_state.players)
		g_game_state.players.append(nick)

		g_game_state.chips[nick] = lowest_chips

		if g_game_state.round != None:
			give_cards(nick)

		say(esc_nick(nick) + ' spielt ab jetzt auf Platz 0,1' + str(1+pos) + reset_colors())
		return True

	if(x_users_say(2, '!poker')):
		text = 'Poker neu gestartet. Befehle sind:'
		for befehl, erklaerung in sorted(help.items()):
			text +=  ' [' + befehl + '] = ' + erklaerung
		say(text)

		g_game_state.active = True
		g_game_state.players = []
		g_game_state.chips = {}
		g_game_state.cards = {}
		g_game_state.round = None
		g_game_state.whos_turn = None

		return

	if not g_game_state.active:
		return

	if(irc_text == 'join'):
		join()
		return

	if(irc_text == 'rank'):
		rank()
		return

	if irc_text.split()[0] in help.keys() and not nick in g_game_state.players:
		say(esc_nick(nick) + ': Um mitzuspielen schreibe join :)')
		return

	def check_turn(quiet=False):
		if g_game_state.cards and not nick in g_game_state.cards:
			if not quiet: say(esc_nick(nick) + ': Du spielst noch nicht mit')
			return False

		if g_game_state.whos_turn != None and g_game_state.players[g_game_state.whos_turn] == nick:
			return True
		else:
			if not quiet: say(esc_nick(nick) + ': Du kommst später dran')
			return False

	def next_turn():
		g_game_state.whos_turn += 1
		skip_foldeds()

		if g_game_state.whos_turn >= len(g_game_state.players):
			g_game_state.whos_turn = None
			g_game_state.round += 1

	def fold(parts):
		g_game_state.folded[nick] = True
		g_game_state.cards[nick] = None		

		num_folded = 0
		not_folded = None
		for player in g_game_state.players:
			if player in g_game_state.folded:
				num_folded += 1
			else:
				not_folded = player

		if num_folded == len(g_game_state.players) - 1:

			g_game_state.chips[not_folded] += g_game_state.pot
			say(underline() + not_folded + ' bekommt die ' + str(g_game_state.pot) + ' Chips')
			reset_round()

		elif num_folded == len(g_game_state.players):
			reset_round()
		else:
			text = underline() + esc_nick(nick)

			if parts:
				text += ' spielt nicht mehr mit'
			else:
				text += ' schaut in dieser Runde zu'

			say(text)

			if not check_turn(True): return
			next_turn()
			loop_ask()

	if(irc_text == 'part'):
		if g_game_state.round != None:
			fold(True)
		else:
			say(nick + ' spielt nicht mehr mit')
		g_game_state.players.remove(nick)
		if nick in g_game_state.chips: del(g_game_state.chips[nick])
		if nick in g_game_state.cards: del(g_game_state.cards[nick])
		return

	if(irc_text == 'ask'):
		loop_ask()
		return

	if irc_text.split()[0] in help.keys() and g_game_state.round == None:
		say(esc_nick(nick) + ': Die Runde hat noch nicht begonnen')
		return

	def invest(player):
		einsatz = g_game_state.einsatz
		all_in = False
		if einsatz >= g_game_state.chips[player]:
			einsatz = g_game_state.chips[player]
			all_in = True

		g_game_state.chips[player] -= einsatz
		g_game_state.pot += einsatz
		g_game_state.gesetzt = True
		
		text = underline() + esc_nick(player) + ' setzt '		
		text += str(einsatz) + ' Chips'
		
		if all_in:
			text += '. Er geht all in'

		say(text)

	def call(player):
		invest(player)
		next_turn()
		loop_ask()
		
	if(irc_text == 'call'):
		if not check_turn(): return
		call(nick)
		return

	if g_game_state.round != None:
		if(x_users_say(2, 'take')):
			call(g_game_state.players[g_game_state.whos_turn])
			return

	if(irc_text[:5] == 'raise'):
		if not check_turn(): return		

		percent = 5

		try:
			percent = int(float(irc_text[5:]))
		except Exception as e:
			pass

		if percent < 0: percent = 0
		if percent > 100: percent = 100
		percent = int(percent)

		_raise = (g_game_state.chips[nick] - g_game_state.einsatz) * percent / 100
		if _raise < 0: _raise = 0
		_raise = int(_raise)

		g_game_state.einsatz += _raise
		invest(nick)

		next_turn()
		loop_ask()
		return

	if(irc_text == 'fold'):
		fold(False)
		return

	if(irc_text == 'check'):
		if not check_turn(): return

		if g_game_state.round == 0:
			say(esc_nick(nick) + ': In der ersten Runde musst du Chips setzen oder folden')
		elif g_game_state.gesetzt:
			say(esc_nick(nick) + ': Wenn vor dir jemand Chips gesetzt hat, musst du setzen oder folden')
		else:
			say(underline() + esc_nick(nick) + ' setzt nichts')
			next_turn()
			loop_ask()
		return

HANDLERS = {"pubmsg":pubmsg}
