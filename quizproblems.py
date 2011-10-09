from modules.quiz import Problem, EASY, MEDIUM, HARD

source_count=0
def get_source():
	global source_count
	source_count += 1
	return __name__+"#%d" % source_count
PROBLEMS = [ \
	Problem( "\"Lothar Meister\" ist der Name zweier Personen, die für die selbe Tätigkeit berühmt wurden. Welche ist das?",
		["Radrennfahrer","Radsportler","Radfahrer","Radler"],
		level=HARD,
		url="http://de.wikipedia.org/wiki/Lothar_Meister",
		source=get_source(), author="syslock",
		tags=["Sport","Geschichte"] ),
]

