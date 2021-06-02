import json
import pandas as pd
import numpy as np
import random
from collections import Counter
import sys

from src.func import tweet_utils
from src.func import regex
from src.func import labmtgen
from src.scripts.process_tweets import *

from labMTsimple.storyLab import *

### This file contains prior version of some tweet cleaning utilities

def geotweets_to_ngrams(geotweet_path):

    tweets = load_tweets(geotweet_path)
    park_tweets, control_tweets, park_names = park_control_split(tweets)
    # get names of parks for removal from sentiment analysis
    park_ngram_stopwords = get_park_stopwords(park_names)
    park_ngrams = tweets_to_ngrams(park_tweets)
    control_ngrams = tweets_to_ngrams(control_tweets)
    return park_ngrams, control_ngrams, park_ngram_stopwords

def park_control_split(tweets):
    # get park tweets
    park_tweets = []
    control_tweets = []
    control_stack = []
    park_names = []
    # get park tweets, control tweets, and park names for stop words
    for tweet in tweets:
        if pd.isnull(tweet['pure_text']) or tweet_utils.is_retweet(tweet):
            continue
        elif pd.isnull(tweet['ParkID']):
            control_stack.append(tweet)
        else:
            park_tweets.append(tweet)
            control_tweets.append(control_stack.pop())
            try:
                park_names.append(str(tweet['Park_Name']).lower())
            except AttributeError:
                print(tweet)
                sys.exit(1)
    return park_tweets, control_tweets, park_names

def sample_ngrams(ngrams, sample = .8):
    ngram_list = ' '.join([' '.join([k] * v)
                          for k, v in ngrams.items()]).split()
    total = len(ngram_list)
    samples = total*sample
    ngram_sample = np.random.choice(ngram_list, int(samples), replace=False)
    return Counter(ngram_sample)


def bootstrap_sentiment_ngrams(park_tweets, control_tweets, stops, sample=.8, n=100):
    park_ngrams = tweets_to_ngrams(park_tweets)
    control_ngrams = tweets_to_ngrams(control_tweets)
    park_sentis = []
    control_sentis = []
    for i in range(n):
        park_sample = sample_ngrams(park_ngrams, sample)
        control_sample = sample_ngrams(control_ngrams, sample)
        park_sentis.append(senti(park_sample, stops))
        control_sentis.append(senti(control_sample, stops))
    return park_sentis, control_sentis

    def bootstrap_bumps(park_tweets_by_user, runs = 5):
        park_tweets = []
        control_tweets = []
        parks = []
        bumps = []
        for i in range(runs):
            for tweet_list in park_tweets_by_user.values():
                tweet_choice = random.choice(tweet_list)
                park_tweets.append(tweet_choice['pure_text'])
                control_tweets.append(tweet_choice['control_text'])
                parks.append(tweet_choice['Park_Name'])
            stops  = get_park_stopwords(parks)
            park_ngrams = tweets_to_ngrams(park_tweets)
            control_ngrams = tweets_to_ngrams(control_tweets)
            bump = senti(park_ngrams, stops)-senti(control_ngrams, stops)
            bumps.append(bump)
        return bumps
