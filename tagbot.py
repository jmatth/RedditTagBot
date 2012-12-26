# vim: set expandtab ts=4 sw=4 :
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

    path = str(sys.path[0])
    retDict = yaml.load(file(path+'/tagbot.yaml', 'r'))[section]

    return retDict

try:
    mainConfig = loadConfig()
except AttributeError:
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
lockfile.write('Bot instance started at: ' +
               datetime.now().strftime("%H:%M:%S %m/%d/%y") + "\n")

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
    tag_list = sub_reddits[subreddit]['tags']

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

        matched = False
        for check in tag_list:
            #Break out if the previous iteration found a match
            if matched:
                break

            for condition in tag_list[check]['conditions']:

                if ('url' in tag_list[check]['conditions'][condition]):
                    if not (re.match(
                        tag_list[check]['conditions'][condition]['url'],
                            post.url, re.IGNORECASE)):
                        continue

                if ('title' in tag_list[check]['conditions'][condition]):
                    if not (re.match(
                        tag_list[check]['conditions'][condition]['title'],
                            post.title, re.IGNORECASE)):
                        continue

                if ('selftext' in tag_list[check]['conditions'][condition]):
                    if not (re.match(
                        tag_list[check]['conditions'][condition]['selftext'],
                            post.selftext, re.IGNORECASE)):
                        continue

                # No continues were hit, it's a match.
                print (datetime.utcnow() + ": tagging " + post.id +
                       " with " + tag_list[check]['css_class'] + ".")

                post.set_flair(flair_css_class=
                               tag_list[check]['css_class'])

                collection.insert(
                    {'post_id': post.id,
                     'tagged_as': tag_list[check]['css_class'],
                     'processed_on': datetime.utcnow()})

                matched = True
                break
        if not matched:
            print (datetime.utcnow() + ": no match for " + post.id + ".")
            collection.insert({'post_id': post.id,
                               'match_type': 'none',
                               'processed_on': datetime.utcnow()})

os.remove(lockpath)
