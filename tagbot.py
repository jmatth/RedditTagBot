"""Python bot to tag posts on reddit.com"""
# vim: set expandtab ts=4 sw=4 :
import praw
import re
import os
from datetime import datetime
from optparse import OptionParser, OptionGroup
import sys
import yaml
import pymongo


# Load the ini into a dictionary for either the
# main config values or the tags to look for.
def main():
    """Wrapper method"""

    # Get command line options
    parser = init_options_parser()
    (options, args) = parser.parse_args()

    # Cannot have both --test and --silent options set
    if options.test is True and options.silent is True:
        print "Options -t and -s are incompatible. Only one or the " \
              "other may be used"
        sys.exit(1)

    if options.test:
        print "Test mode enabled. No changes to database or reddit " \
            "posts will be made"

    # load the config file
    main_config = load_config(options.configfile)

    try:
        lockpath = main_config['lockpath']
        db_name = main_config['database']

    except KeyError:
        print "Missing value from main_tagbot_config"
        sys.exit()

    # Write a lockfile to prevent another instance from starting
    # while this one is still running, or exit if it already exits.
    if not write_lockfile(lockpath):
        sys.exit()

    #Open connection to db_name
    connection = pymongo.Connection()
    database = connection[db_name]

    #Now we load the subreddits we want to process.
    #Underscore used in variable name to reduce the
    #risk of confusing typos.
    sub_reddits = load_config(options.configfile, 'subreddits')

    # Remove the lockfile and esit for any exceptions thrown by praw
    # TODO: Catch only praw-specific exception. Currently too general
    # TODO: tagbot.log path should be obtained from tagbot config file
    try:
        for subreddit_name, subreddit_options in sub_reddits.iteritems():
            reddit = praw.Reddit(user_agent=subreddit_options['username']
                                 + " running the reddit tagbot for /r/"
                                 + subreddit_name + ".")
            reddit.login(username=subreddit_options['username'],
                         password=subreddit_options['password'])
            subreddit = reddit.get_subreddit(subreddit_name)

            categories = get_categories(subreddit, subreddit_options)

            for category in categories:
                process_posts(category, subreddit_options['tags'],
                              database[subreddit_name], options.test,
                              options.silent)
    except Exception as ex:
        with open('/tmp/tagbot.log','a') as f:
            f.write(str(ex) + "\n")

    remove_lockfile(lockpath)


def get_categories(subreddit, subreddit_options):
    """Get a dictionary of iterators for the subreddit"""
    return [subreddit.get_hot(limit=subreddit_options['hot_limit']),
            subreddit.get_new(limit=subreddit_options['new_limit']),
            subreddit.get_top(limit=subreddit_options['top_limit'])]


def process_posts(posts, tags, collection, test=False, silent=False):
    """Check a list of posts"""

    for post in posts:

        #Skip post if it's already been checked.
        if (collection.find_one({'post_id': post.id})):
            continue

        matched = False
        for check in tags:
            #Break out if the previous iteration found a match
            if matched:
                break

            for condition in tags[check]['conditions']:

		# Ignore is the link flair has been set manually
                if (post.link_flair_css_class is not None):
                    continue

                if ('url' in tags[check]['conditions'][condition]):
                    if not (re.match(
                        tags[check]['conditions'][condition]['url'],
                            post.url, re.IGNORECASE)):
                        continue

                if ('title' in tags[check]['conditions'][condition]):
                    if not (re.match(
                        tags[check]['conditions'][condition]['title'],
                            post.title, re.IGNORECASE)):
                        continue

                if ('selftext' in tags[check]['conditions']
                        [condition]):
                    if not (re.match(
                        tags[check]['conditions'][condition]
                            ['selftext'], post.selftext, re.IGNORECASE)):
                        continue

                # No continues were hit, it's a match.
                if not silent:
                    print_post_info(post, "TAGGING with " +
                                    tags[check]['css_class'] + ".", "[TAGGED] ")

                # If not in test-mode, update the database and flair
                if not test:
                    post.set_flair(flair_css_class=tags[check]['css_class'],
                                   flair_text=tags[check]['flair_text'])

                    collection.insert(
                        {'post_id': post.id,
                            'tagged_as': tags[check]['css_class'],
                            'processed_on': datetime.now()})

                matched = True
                break

        if not matched:
            if not silent:
                print_post_info(post, "No match found for tagging.", "         ")

            if not test:
                collection.insert({'post_id': post.id,
                                   'match_type': 'none',
                                   'processed_on': datetime.now()})


def print_post_info(post, msg = "", prefix = ""):
    """Outputs information about a post submission"""
    print (datetime.now().strftime("%H:%M:%S %m/%d/%y") +
           ": " + prefix + "(" + post.id + ") {" + 
           post.title.encode('ascii', 'xmlcharrefreplace') + "} " + msg)

def load_config(configfile=None, section='main'):
    """Load the specified config section, or main by default"""
    try:
        if configfile is None:
            path = str(sys.path[0])
            configfile = path+'/tagbot.yaml'
        ret_dict = yaml.load(file(configfile, 'r'))[section]
    except AttributeError:
        print "Config file not found, not readable, or incomplete."
        sys.exit(1)
    except IOError:
        print("Error opening config file at path: " + configfile)
        sys.exit(1)
    return ret_dict


def write_lockfile(lockpath):
    """Write a lockfile with information about current bot instance"""
    if os.path.exists(lockpath):
        print "Already running"
        return False

    lockfile = open(lockpath, 'w')
    lockfile.write('Bot instance started at: ' +
                   datetime.now().strftime("%H:%M:%S %m/%d/%y") + "\n")
    lockfile.close()
    return True

def remove_lockfile(lockpath):
    """Removes the lockfile if it exists"""
    try:
        os.remove(lockpath)
    except OSError:
        pass

# Parse options from the command line
def init_options_parser():
    parser = OptionParser(usage="%prog [-t|-s] [-c <configfile>]",
                          description="Reddit bot for automatic tagging and"
                          " responding to new posts")
    parser.add_option('-t', '--test', action='store_true', help='Print changes'
                      ' without updating the database, changing any flair, or'
                      ' making any posts')
    parser.add_option('-s', '--silent', action='store_true',
                      help='Silent: Do not print any output')
    parser.add_option('-c', '--configfile', action='store',
                      help='Path to yaml config file')
    return parser

if __name__ == "__main__":
    main()
