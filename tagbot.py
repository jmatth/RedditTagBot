# Reddit API
import praw
import re
import os
from datetime import datetime
import sys
import yaml
import pymongo

# Load the ini into a dictionary for either the
# main config values or the tags to look for.
def loadConfig(section='main'):

	retDict = yaml.load(file('tagbot.yaml', 'r'))[section]

	return retDict

try:
	mainConfig = loadConfig()
except AttributError:
	print "Config file not found, not readable, or incomplete."
	sys.exit()

try:
	lockpath = mainConfig['lockpath']
	database = mainConfig['database']

except KeyError:
	print "Missing value from main_tagbot_config"
	sys.exit()

if os.path.exists(lockpath):
	print "Already running"
	sys.exit()

# Write a lockfile to prevent another instance from starting
# while this one is still running.
lockfile = open(lockpath, 'w')
lockfile.write('Bot instance started at: '
				+ datetime.now().strftime("%H:%M:%S %m/%d/%y") + "\n")

#Open connection to database
connection = pymongo.Connection()
db = connection[database]

#Now we load the subreddits we want to process.
#Underscore used in variable name to reduce the
#risk of confusing typos.
sub_reddits = loadConfig('subreddits')

for subreddit in sub_reddits:
	#Use a collection matching the subreddit name
	collection = db[subreddit]

	#Load subreddit specific configs
	reg_list = sub_reddits[subreddit]['tags']

	#Login to reddit
	r = praw.Reddit(user_agent=sub_reddits[subreddit]['username']
					+ " running the reddit tagbot for /r/"
					+ subreddit + ".")

	r.login(username=sub_reddits[subreddit]['username'],
			password=sub_reddits[subreddit]['password'])

	#Get hot posts
	hot = (r.get_subreddit(subreddit)
			.get_hot(limit=sub_reddits[subreddit]['post_limit']))

	for post in hot:

		#Skip post if it's already been checked.
		if (collection.find_one({'post_id': post.id})):
			continue

		for check in reg_list:
			if ('url' in reg_list[check]) and \
			(re.match(reg_list[check]['url'], post.url, re.IGNORECASE)):
				post.set_flair(flair_css_class=reg_list[check]['css_class'])
				collection.insert({'post_id': post.id, 'match_type': 'url',
									'matched_with': reg_list[check]['url'],
									'tagged_as': reg_list[check]['css_class'],
									'processed_on': datetime.utcnow()})
				break
			elif ('title' in reg_list[check]) and \
			(re.match(reg_list[check]['title'], post.url, re.IGNORECASE)):
				post.set_flair(flair_css_class=reg_list[check]['css_class'])
				collection.insert({'post_id': post.id,
									'match_type': 'title',
									'matched_with': reg_list[check]['title'],
									'tagged_as': reg_list[check]['css_class'],
									'processed_on': datetime.utcnow()})
				break

		else:
			collection.insert({'post_id': post.id,
								'match_type': 'none',
								'processed_on': datetime.utcnow()})

os.remove(lockpath)
