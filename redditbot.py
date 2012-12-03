# Reddit API
import praw
import re
import os
from datetime import datetime
import sys
import ConfigParser
import pymongo

def loadTagConfig(configFile = "redditbot.ini"):
	retDict = dict()

	conf = ConfigParser.ConfigParser()
	conf.read(configFile)

	for section in conf.sections():
		retDict[section] = dict(conf.items(section))

	return retDict

lockpath = '/var/redditbot/mechanicalkeyboards.lock'

subreddit = 'mechanicalkeyboards'

post_limit = 5

if os.path.exists(lockpath):
	print "Already running"
	sys.exit()

#Open connection to database
connection = pymongo.Connection()
db = connection.redditbot_mechanicalkeyboards_test
collection = db.processed_posts

# Write a lockfile to prevent another instance from starting
# while this one is still running.
lockfile = open(lockpath, 'w')
lockfile.write('Bot instance started at: ' + datetime.now().strftime("%H:%M:%S %m/%d/%y") + "\n")

reg_list = loadTagConfig()

r = praw.Reddit(user_agent="TransistorRevolt testing the /r/mechanicalkeyboards bot.", site_name='mechanicalkeyboards')

r.login()

hot = r.get_subreddit(subreddit).get_hot(limit=post_limit)

for post in hot:

	#Skip post if it's already been checked.
	if (collection.find_one({'post_id': post.id})):
		continue

	for check in reg_list:
		if ('url' in reg_list[check]) and (re.match(reg_list[check]['url'], post.url)):
			post.set_flair(flair_css_class=reg_list[check]['css_class'])
			collection.insert({'post_id': post.id, 'match_type': 'url', 'matched_with': reg_list[check]['url'], 'tagged_as': reg_list[check]['css_class']})
			break
		elif ('title' in reg_list[check]) and (re.match(reg_list[check]['title'], post.url)):
			post.set_flair(flair_css_class=reg_list[check]['css_class'])
			collection.insert({'post_id': post.id, 'match_type': 'title', 'matched_with': reg_list[check]['title'], 'tagged_as': reg_list[check]['css_class']})
			break

	else:
		collection.insert({'post_id': post.id, 'match_type': 'none'})
	

os.remove(lockpath)
