import random
import math
import time

g_op_nick = None
g_active  = None

g_pot     = None
g_einsatz = None
g_cards   = None

g_round     = None
g_whos_turn = None

g_players = None
g_chips   = None
g_folded  = None

g_flop      = None
g_checked   = None
g_last_time = None

def irc_join(plugin, connection, event):
	g_op_nick = False

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
pic_num = 13

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

def esc_nick(nick):
	return nick[:1] + '' + nick[1:]

def rank_hand_names():
	rank_colors = [
	'7,8',
	'1,9',
	'1,13',
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

g_pictures = ['2', '3', '4', '5', '6', '7', '8', '9', '10', '11B', '13D', '7K', '8A']

for i in range(9):
	g_pictures[i] = '0' + g_pictures[i]

for i in range(13):
	g_pictures[i] = '' + g_pictures[i] + ''

g_colors = ['0,1♠', '0,1♣', '4,1♥', '4,1♦']
for i in range(4):
	g_colors[i] = '1,1.' + g_colors[i]

def card_name(card_idx):	
	name = g_colors[card_color(card_idx)] + g_pictures[card_picture(card_idx)]
	if card_picture(card_idx) != pic_10:
		name += '1,1.'
	return name + reset_colors()

def picture_name(card_idx):
	pictures = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'B', 'D', 'K', 'A']
	return pictures[card_picture(card_idx)]

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
	global g_deck
	g_deck = []
	for i in range(52):
		g_deck.append(i)
	random.seed()
	for i in range(300):
		pos1 = random.randint(0, 51)
		pos2 = random.randint(0, 51)
		temp = g_deck[pos1]
		g_deck[pos1] = g_deck[pos2]
		g_deck[pos2] = temp

def take_card():
	global g_deck
	card = g_deck[-1]
	g_deck = g_deck[:-1]
	return card

def group(number):
    s = '%d' % number
    groups = []
    while s and s[-1].isdigit():
        groups.append(s[-3:])
        s = s[:-3]
    return s + '.'.join(reversed(groups))

def cards_desc(cards):
	cards = sorted(cards)
	text = ':'
	for card in cards:
		text += ' ' + card_name(card)
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
	return '4' + text + reset_colors()

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

def pubmsg(plugin, connection, event):
	global g_active
	global g_cards
	global g_pot
	global g_einsatz
	global g_chips
	global g_folded
	global g_players		
	global g_round
	global g_whos_turn
	global g_op_nick
	global g_last_time
	global g_checked

	channel = event.target()
	nick = event.source().split('!')[0]
	irc_text = event.arguments()[0]

	def say(text):
		try: # wegen unicode
			connection.privmsg(channel, text)
		except Exception as e:
			pass

	def notice(nick, text):
		try: # wegen unicode
			connection.notice(nick, text)
		except Exception as e:
			pass

	def may_check():
		global g_round
		global g_whos_turn
		global g_checked
		return g_round > 0 and (g_whos_turn == 0 or g_checked)

	join_hint = 'Wer möchte, kann jetzt join schreiben, um mitzuspielen.'

	def give_pot(player):
		global g_chips
		global g_pot
		global g_round
		g_chips[player] += g_pot
		say(colored(player) + ': Du bekommst den Pot und hast nun ' + str(g_chips[player])\
		+ ' Chips. ' + join_hint)
		g_round = None

	def pot_desc():
		global g_pot
		return 'Im Pot sind ' + str(g_pot) + ' Chips.'

	def skip_foldeds():
		global g_whos_turn
		while g_whos_turn < len(g_players):
			if g_players[g_whos_turn] not in g_folded: break
			g_whos_turn += 1			

	def iter_ask():
		global g_pot
		global g_einsatz
		global g_cards
		global g_round
		global g_whos_turn
		global g_chips
		global g_folded
		global g_flop
		global g_checked
		global g_players
		global g_last_time

		g_last_time = time.time()

		if g_round == None:
			g_pot = 0
			g_einsatz = 10
			g_cards = {}
			g_folded = {}
			g_round = 0
			g_whos_turn = None
			g_flop = None

		solvent_players = 0
		for player in g_players:
			if player not in g_folded:
				if g_chips[player] > 0: solvent_players += 1

		if solvent_players == 0:
			do_say = False
		else:
			do_say = True

		if g_round == 0:
			if g_whos_turn == None:
				reset_deck()
				for player in g_players:
					g_cards[player] = []
					cards = g_cards[player]
					cards.append(take_card())
					cards.append(take_card())

				g_checked = False
				g_whos_turn = 0
				skip_foldeds()

				say('Runde 1: PREFLOP. Jeder bekommt zwei Karten.')

				for player in g_players:
					if player not in g_folded:
						notice(player, 'Deine Karten sind' + cards_desc(g_cards[player]))

		elif g_round == 1:
			if g_whos_turn == None:
				g_flop = []
				for i in range(3):
					g_flop.append(take_card())

				g_checked = False
				g_whos_turn = 0
				skip_foldeds()

				if do_say: say('Runde 2: FLOP' + cards_desc(g_flop))

		elif g_round == 2:
			if g_whos_turn == None:
				g_flop.append(take_card())

				g_checked = False
				g_whos_turn = 0
				skip_foldeds()

				if do_say: say('Runde 3: TURN CARD' + cards_desc(g_flop))

		elif g_round == 3:
			if g_whos_turn == None:
				g_flop.append(take_card())

				g_checked = False
				g_whos_turn = 0
				skip_foldeds()

				say('Letzte Runde: RIVER CARD' + cards_desc(g_flop))

		elif g_round == 4:
			highest = -1
			highest_desc = None
			winners = []
			for player in g_players:
				if player not in g_folded:
					hand, desc = check_seven(g_cards[player] + g_flop)
					if hand > highest:
						highest = hand
						highest_desc = desc
						winners = [player]
					elif hand == highest:
						winners.append(player)
			
			split = int(g_pot / len(winners))
			
			for winner in winners:
				g_chips[winner] += split

			if len(winners) > 1:
				text = 'Es gewinnen '
			else:
				text = 'Es gewinnt '

			farbig = '8,4'
			text += farbig

			iter = 0
			for winner in winners:				
				text += esc_nick(winner)
				if iter < len(winners) - 1:
					text += reset_colors() + ' und ' + farbig
				iter += 1

			text += reset_colors() + ' mit '
			if len(winners) > 1: text += 'jeweils '

			text += hand_name(highest) + ' ' + highest_desc

			if len(winners) > 1:
				text += '. Jeder bekommt '
			else:
				text += '. Er bekommt '

			text += str(split) + ' Chips. Es führt '
			
			iter = 0		
			for player in sorted(g_chips, key=g_chips.get, reverse=True):
				if g_chips[player] > 0:
					chips = str(g_chips[player])
				else:
					chips = 'out'
				text += player + ' (' + chips + ')'
				if iter < len(g_chips) - 1:
					if iter == 0:
						text += ', gefolgt von '
					else:
						text += ', '
				iter += 1
			text += '.'

			say(text + ' ' + join_hint)
			g_round = None

			to_remove = []
			for player in g_players:
				if g_chips[player] <= 0:
					to_remove.append(player)

			for player in to_remove:
				g_players.remove(player)
				g_cards[player] = None

			return

		if g_round < 4:
			if may_check():
				check = 'check, '
			else:
				check = ''

			player = g_players[g_whos_turn]

			if g_chips[player] <= 0:
				next_turn()
				return True
			else:
				say(colored(esc_nick(g_players[g_whos_turn])) + ': ' + pot_desc() + ' Du hast ' + str(g_chips[player])\
				+ ' Chips. Der Einsatz ist ' + str(g_einsatz) + ' Chips. Willst du ' + check + 'call, raise oder fold?')
	
	def loop_ask():
		while iter_ask(): None

	def isop():
		global g_op_nick
		return nick == g_op_nick

	def notop():
		say(esc_nick(nick) + ': ' + g_op_nick + ' hat Poker schon gestartet.')

	def setop():
		global g_op_nick
		if g_op_nick:
			notop()
		else:
			g_op_nick = nick
			# say(esc_nick(nick) + ': Du darfst sofort stop benutzen, andere müssten davor 3 Minuten warten.')

	def join():
		global g_round
		global g_chips
		if nick in g_players:
			say(esc_nick(nick) + ': Du spielst bereits mit.')
			return False
		if g_round != None:
			say(esc_nick(nick) + ': Bitte zu Beginn der nächsten Runde einsteigen.')
			return False
		pos = len(g_players)
		g_players.append(nick)
		say(esc_nick(nick) + ': Du spielst ab jetzt mit auf Platz 0,1' + str(1+pos) + reset_colors() + '.')
		g_chips[nick] = 500
		return True

	if(irc_text == '!poker'):
		if not g_active:
			g_last_time = time.time()

			help = [
			[ 'stop', 'Poker beenden' ],
			[ 'join', 'Mitspielen' ],
			[ 'ask' , 'Runde beginnen oder weitermachen' ],
			[ 'look', 'Karten ansehen' ],
			[ 'part', 'Nicht mehr mitspielen' ],
			[ 'players', 'Mitspieler anzeigen' ] ]

			text = 'Poker gestartet. Kein ! benutzen. Befehle sind:'
			for befehl in help:
				text +=  ' ' + befehl[0] + ' = ' + befehl[1] + '.'
			say(text)
		else:
			say('Poker läuft schon, schreibe stop, wenn du es beenden willst.')
			return

		g_active = True
		if not g_op_nick: setop()

		if isop():
			g_players = []
			g_chips = {}
			g_round = None

		if not join(): return

	if(irc_text == 'stop'):
		if g_active:
			if isop() or g_last_time < time.time() - 180:
				g_active = False
				g_op_nick = None
				say('Poker wurde beendet.')
			else:
				say('Nur der Poker-Operator darf stop benutzen, andere müssen 3 Minuten warten.')

	if not g_active:
		return

	if(irc_text == 'join'):
		if not join(): return

	if irc_text.split()[0] in [
	'part',
	'players',
	'ask',
	'look',
	'call',
	'raise',
	'fold' ] and not nick in g_players:
		say(esc_nick(nick) + ': Du willst mitspielen? Schreibe join, sobald eine Runde geendet hat.')
		return

	if(irc_text == 'part'):
		g_players.remove(nick)
		g_cards[nick] = None
		say(esc_nick(nick) + ': Ok, du spielst ab jetzt nicht mehr mit.')

	if(irc_text == 'players'):
		joined = 'es spielen: '
		for player in g_players:
			joined += player + ', '
		say(joined[:-2])

	if(irc_text == 'ask'):
		# if not isop():
		#	notop()
		# else:
		loop_ask()

	if not g_cards: return

	if(irc_text == 'look'):
		if nick in g_folded:
			say('Du hast keine Karten, weil du gefolded hast.')
		else:
			notice(nick, cards_desc(g_cards[nick]) + ' Du hast ' + str(g_chips[nick]) + ' Chips.')

	def check_turn():
		if g_cards and not nick in g_cards:
			say(esc_nick(nick) + ': Du spielst noch nicht mit.')
			return False

		if g_whos_turn != None and g_players[g_whos_turn] == nick:
			return True
		else:
			say(esc_nick(nick) + ': Du kommst später dran.')
			return False

	def next_turn():
		global g_whos_turn
		global g_round

		g_whos_turn += 1
		skip_foldeds()

		if g_whos_turn >= len(g_players):
			g_whos_turn = None
			g_round += 1

	def einsatz(_raise):
		global g_chips
		global g_pot
		einsatz = g_einsatz
		all_in = False
		if einsatz >= g_chips[nick]:
			einsatz = g_chips[nick]
			all_in = True
		g_chips[nick] -= einsatz
		g_pot += einsatz
		
		text = esc_nick(nick) + ': Ok, '		
		if _raise != None: text += 'um ' + str(_raise) + ' Chips erhöht und '
		text += str(einsatz) + ' Chips gesetzt. '
		
		if all_in:
			text += 'Du gehst all in.'
		else:
			text += 'Du hast noch ' + str(g_chips[nick]) + ' Chips.'
		say(text)

	if(irc_text == 'call'):
		if not check_turn(): return
		einsatz(None)
		g_checked = False
		next_turn()
		loop_ask()

	if(irc_text[:5] == 'raise'):
		if not check_turn(): return
		_raise = 10
		try:
			_raise = int(float(irc_text[5:]))
		except Exception as e:
			pass
		if g_einsatz + _raise > g_chips[nick]:
			say(colored(esc_nick(nick)) + ': ' + str(g_einsatz + _raise) + ' Chips Einsatz hast du nicht.')
			# loop_ask()
			return
		g_einsatz += _raise
		einsatz(_raise)
		g_checked = False
		next_turn()
		loop_ask()

	if(irc_text == 'fold'):
		if not check_turn(): return
		g_folded[nick] = True
		g_cards[nick] = None		
		# g_checked = False

		num_folded = 0
		not_folded = None
		for player in g_players:
			if player in g_folded:
				num_folded += 1
			else:
				not_folded = player

		text = esc_nick(nick) + ': Ok, du bist in dieser Runde draussen.'

		if num_folded == len(g_players) - 1:
			say(text)
			give_pot(not_folded)
		elif num_folded == len(g_players): # wenn man allein gespielt hat
			say(text + ' Schreibe ask, um weiterzumachen. ' + join_hint)
			g_round = None
		else:
			say(text)
			next_turn()
			loop_ask()

	if(irc_text == 'check'):
		if not check_turn(): return
		if may_check():
			say(esc_nick(nick) + ': Ok, du machst keinen Einsatz.')
			g_checked = True
			next_turn()
			loop_ask()
		else:
			if g_round == 0:
				say(nick + ': Im Preflop kannst du nicht checken.')
			elif g_whos_turn > 0 and not g_checked:
				say(nick + ': Du kannst nur checken, wenn alle vor dir auch checken.')
			else:
				say(nick + ': Du kannst nicht checken.')

HANDLERS = {"pubmsg":pubmsg, "join":irc_join}
