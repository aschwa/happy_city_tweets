import json
import pandas as pd
from datetime import datetime
from src.func import tweet_utils
from src.func import regex


def load_tweets(geotweet_path):
    with open(geotweet_path, 'r') as f:
        tweets = json.load(f)
    return remove_duplicates(tweets)


def remove_duplicates(tweets):
    df = pd.DataFrame.from_records(tweets)
    df.drop_duplicates(subset='id_str', inplace=True)
    tweets = df.to_dict('records')
    return tweets


def bad_tweet_filter(tweet, hashtag_list):
    if pd.isnull(tweet['pure_text']):
        return True
    tweet_ngrams = dict(regex.get_ngrams(tweet['pure_text'],
                        path='ngrams.bin'))
    if tweet_utils.is_retweet(tweet):
        return True
    # check Date
    ts = tweet['tweet_created_at']
    day = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
    if day > datetime(2015, 4, 27):
        return True
    if any(x in tweet_ngrams.keys() for x in hashtag_list):
        return True
    return False


def user_control_split(tweets, hashtag_list=["#job"]):
    park_users = {}
    # print("Building list of park users")
    for tweet in tweets:
        if pd.isnull(tweet['ParkID']):
            continue
        else:
            park_users[tweet['user']['id_str']] = []
    # print("Park Users {}".format(len(park_users)))
    # print("Finding all park tweets and their control tweets")
    control_stack = []
    for tweet in tweets:
        this_user = tweet['user']['id_str']
        # If bad tweet, skip it
        if bad_tweet_filter(tweet, hashtag_list):
            continue
        # Not a park tweet, add to park user or control stack
        elif pd.isnull(tweet['ParkID']):
            # park user tweet, add to their tweets
            try:
                park_users[this_user].append(tweet)
            # not a park user, add to control stack
            except KeyError:
                control_stack.append(tweet)
        # It is a park tweet!
        else:
            tweet["control_text"] = control_stack.pop()['pure_text']
            park_users[this_user].append(tweet)
    return park_users
