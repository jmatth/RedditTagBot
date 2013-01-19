# Reddit Tagbot
Tagbot is an easy to configure python script that can be used to mark certain posts in your subreddit.

NOTE: While it is currently usable, it is still under active development and it is likely that the config file format and database design will change in the near future. If you insist on using it now, please be aware of this and don't get too attached to your config files.

## Dependencies
[Python Reddit API Wrapper (PRAW)](https://github.com/praw-dev/praw)

If you don't already have this, install it with `pip install praw`.

PyYAML

For processing config files.

MongoDB and pyMongo

This is used to store information about posts that have already been processed by the bot. This both acts as a log, and prevents unneeded API calls by skipping any posts that have already been handled.

To install all needed python modules, simply cd into the project directory and run `pip install -r requirements.txt`.

## Configuration
Tagbot is configured with a single YAML file with two main sections:

* Main: This contains basic configuration information like where to put the lockfile and the MongoDB database to use.

* Subreddits: This is where you can configure what subreddits the bot will process and what to look for in each one. NOTE: if you want to run this bot on multiple subreddits, you should specify them all in the same config file instead of running multiple instances of the bot. This is because PRAW automatically limits the number of API calls to one request every two seconds [as per the Reddit Devs request](https://github.com/mellort/reddit_api#faq). If you run multiple instances of the bot at the same time, it is very likely you will exceed this.

See the provided example config file to get started.
