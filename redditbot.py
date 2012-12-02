# Import the reddit API wrapper
import praw
# Import regex module
import re
# Import os for touching lock files
import os
# Import datetime for timestamping lock files
from datetime import datetime
import sys

lockpath = '/var/redditbot/mechanicalkeyboards.lock'

subreddit = 'mechanicalkeyboards'

post_limit = 5

if os.path.exists(lockpath):
	print "Already running"
	sys.exit()

# Write a lockfile to prevent another instance from starting
# while this one is still running.
lockfile = open(lockpath, 'w')
lockfile.write('Bot instance started at: ' + datetime.now().strftime("%H:%M:%S %m/%d/%y") + "\n")

reg_list = {}

reg_list['geekwhack'] = {'title': re.compile('[Gg]eekhack'), 'url': re.compile('.*geekhack\.org.*'), 'css_class': 'geekwhack'}

reg_list['imgur'] = {'title': re.compile('imgur'), 'url': re.compile('.*imgur.*'), 'css_class': 'imgur'}

r = praw.Reddit(user_agent="TransistorRevolt testing the /r/mechanicalkeyboards bot.", site_name='mechanicalkeyboards')

r.login()

hot = r.get_subreddit(subreddit).get_hot(limit=post_limit)

for post in hot:
	for check in reg_list:
		if (reg_list[check]['url'].match(post.url)) or (reg_list[check]['title'].match(post.title)):
			post.set_flair(flair_css_class=reg_list[check]['css_class'])
			break
	

os.remove(lockpath)
