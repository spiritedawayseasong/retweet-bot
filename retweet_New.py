#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, tweepy, inspect, hashlib
from datetime import datetime, timedelta
import time
from dotenv import load_dotenv
import GetOldTweets3 as got
import twint
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

# retrieve last savepoint if available
try:
    with open(last_id_file, "r") as file:
        savepoint = file.read()
except IOError:
    savepoint = ""
    print("No savepoint found. Bot is now searching for results")

start = '202204011415'
end = '202204011430'
# start = '2022-03-19'
# end = '2022-03-20'
# c = twint.Config()
# c.Search = hashtag

while start != '202204070000':
    # search query
    timelineIterator = tweepy.Cursor(api.search_30_day, label='development', query=hashtag, fromDate=start, toDate=end).items(100)
    # tweetCriteria = got.manager.TweetCriteria().setQuerySearch(hashtag) \
    #     .setSince(start) \
    #     .setUntil(end)
    # tweets = got.manager.TweetManager.getTweets(tweetCriteria)
    # c.Since = start
    # c.Until = end
    # tweets = twint.run.Search(c)
    # put everything into a list to be able to sort/filter
    timeline = []
    for status in timelineIterator:
        timeline.append(status)

    if timeline:
        try:
            last_tweet_id = timeline[0].id
        except IndexError:
            last_tweet_id = savepoint

        # filter @replies/blacklisted words & users out and reverse timeline
        #timeline = filter(lambda status: status.text[0] = "@", timeline)   - uncomment to remove all tweets with an @mention
        timeline = filter(lambda status: not any(word in status.text.split() for word in wordBlacklist), timeline)
        timeline = filter(lambda status: status.author.screen_name not in userBlacklist, timeline)
        timeline = list(timeline)
        timeline.reverse()

        tw_counter = 0
        err_counter = 0

        if timeline:
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
                    print(e)
                    continue

            print("Finished. %d Tweets retweeted, %d errors occured." % (tw_counter, err_counter))

    # start = (datetime.strptime(start, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
    # end = (datetime.strptime(end, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
    start = (datetime.strptime(start, '%Y%m%d%H%M') + timedelta(minutes=15)).strftime('%Y%m%d%H%M')
    end = (datetime.strptime(end, '%Y%m%d%H%M') + timedelta(minutes=15)).strftime('%Y%m%d%H%M')
    # if timeline:
    #     time.sleep(60)

# write last retweeted tweet id to file
with open(last_id_file, "w") as file:
    file.write(str(last_tweet_id))
