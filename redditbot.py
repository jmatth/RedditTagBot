# Import the reddit API wrapper
import praw
# Import regex module
import re
# Import os for touching lock files
import os
# Import datetime for timestamping lock files
import datetime from datetime

if os.path.exists('/var/redditbot/mechanicalkeyboards.lock'):
	print "Already running"
	return

# Write a lockfile to prevent another instance from starting
# while this one is still running.
lockfile = open('/var/redditbot/mechanicalkeyboards.lock', 'w')
lockfile.write('Bot instance started at: ' + datetime.now().strftime("%H:%M:%S %m/%d/%y"))


r = praw.Reddit(user_agent="TransistorRevolt testing the mechanicalkeyboards bot.")

r.login('username', 'password')

top = r.get_subreddit('mechanicalkeyboards').get_hot(limit=5)

for x in top:
	#TODO: write code
