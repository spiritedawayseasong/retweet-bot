#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, configparser, tweepy, inspect, hashlib
from dotenv import load_dotenv
load_dotenv()

path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# your hashtag or search query and tweet language (empty = all languages)
hashtag = os.getenv("search_query")
tweetLanguage = os.getenv("tweet_language")

# Number retweets per time
num = int(os.getenv("number_of_rt"))

# blacklisted users and words
userBlacklist = []
wordBlacklist = ["RT", u"♺"]

# build savepoint path + file
hashedHashtag = hashlib.md5(hashtag.encode('ascii')).hexdigest()
last_id_filename = "last_id_hashtag_%s" % hashedHashtag
rt_bot_path = os.path.dirname(os.path.abspath(__file__))
last_id_file = os.path.join(rt_bot_path, last_id_filename)

# create bot
auth = tweepy.OAuthHandler(os.getenv("consumer_key"), os.getenv("consumer_secret"))
auth.set_access_token(os.getenv("access_token"), os.getenv("access_token_secret"))
api = tweepy.API(auth, wait_on_rate_limit=True)

lastTweet = api.user_timeline(user_id=1514646076363522054, count=1, exclude_replies=True, include_rts=True, trim_user=True)
lastTweetId = lastTweet[0].retweeted_status.id
# search query
timelineIterator = tweepy.Cursor(api.search_tweets, q=hashtag, since_id=lastTweetId, lang=tweetLanguage).items(num)

# put everything into a list to be able to sort/filter
timeline = []
for status in timelineIterator:
    timeline.append(status)

# filter @replies/blacklisted words & users out and reverse timeline
#timeline = filter(lambda status: status.text[0] = "@", timeline)   - uncomment to remove all tweets with an @mention
timeline = filter(lambda status: not any(word in status.text.split() for word in wordBlacklist), timeline)
timeline = filter(lambda status: status.author.screen_name not in userBlacklist, timeline)
timeline = list(timeline)
timeline.reverse()

tw_counter = 0
err_counter = 0

# iterate the timeline and retweet
for status in timeline:
    try:
        print("(%(date)s) %(name)s: %(message)s\n" % \
              {"date": status.created_at,
               "name": status.author.screen_name.encode('utf-8'),
               "message": status.text.encode('utf-8')})

        api.retweet(status.id)
        tw_counter += 1
    except tweepy.errors.TweepyException as e:
        # just in case tweet got deleted in the meantime or already retweeted
        err_counter += 1
        # print e
        continue

print("Finished. %d Tweets retweeted, %d errors occured." % (tw_counter, err_counter))
