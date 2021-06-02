import pandas as pd
import random

from src.func import tweet_utils
from src.func import regex
from src.func import labmtgen
from src.scripts.process_tweets import *

from labMTsimple.storyLab import *


def get_tweets_timestamp(park_user_tweets):
    """
    Take a list of lists (tweets by user) and assigns a random control tweet. Returns a list of tweets.
    Each item in return list has in-park tweet text, control tweet tet, park name, nimestamp.
    Args:
        park_user_tweets (list]): [description]

    Returns:
        [list]: [List of park tweets]
    """   
    park_tweet_list = []
    for user, tweet_list in park_user_tweets.items():
        tweet_count = len(tweet_list)
        tweet_list_parks = [tweet for tweet in tweet_list
                            if not pd.isnull(tweet['ParkID'])]
        park_tweet_count = len(tweet_list_parks)
        not_park_count = tweet_count-park_tweet_count
        if park_tweet_count > 0 and not_park_count > 0:
            tweet_choice = random.choice(tweet_list_parks)
            park_text = tweet_choice['pure_text']
            control_text = tweet_choice['control_text']
            tweet_time = tweet_choice['tweet_created_at']
            park_name = tweet_choice['Park_Name']
            park_tweet_list.append({'park_text': park_text,
                                    'control_text': control_text,
                                    'park_name': park_name,
                                    'tweet_created_at': tweet_time})
    return park_tweet_list


def get_time_control_text_park(park_user_tweets):
    """
    Take a list of lists (tweets by user) and assigns a random control tweet based on timestamp. Returns a list of tweets.
    Each item in return list has in-park tweet text, control tweet tet, park name, nimestamp.
    Args:
        park_user_tweets (list]): [description]

    Returns:
        [list]: [List of park tweets]
    """     
    park_tweet_list = []
    for user, tweet_list in park_user_tweets.items():
        tweet_count = len(tweet_list)
        tweet_list_parks = [tweet for tweet in tweet_list
                            if not pd.isnull(tweet['ParkID'])]
        park_tweet_count = len(tweet_list_parks)
        not_park_count = tweet_count-park_tweet_count
        if park_tweet_count > 0 and not_park_count > 0:
            tweet_choice = random.choice(tweet_list_parks)
            park_text = tweet_choice['pure_text']
            control_text = tweet_choice['control_text']
            park_name = tweet_choice['Park_Name']
            park_id = tweet_choice['ParkID']
            park_tweet_list.append({'park_id': park_id,
                                    'park_name': park_name,
                                    'park_text': park_text,
                                    'control_text': control_text})
    return park_tweet_list


def get_both_control_text(park_user_tweets):
    """
    Take a list of lists (tweets by user) and assigns a random control tweet based on timestamp and a random control tweet from same user. Returns a list of tweets.
    Each item in return list has in-park tweet text, control tweet tet, park name, nimestamp.
    Args:
        park_user_tweets (list]): [description]

    Returns:
        [list]: [List of park tweets]
    """     
    park_tweet_text = []
    user_tweet_text = []
    time_tweet_text = []
    park_list = []
    for user, tweet_list in park_user_tweets.items():
        tweet_list_parks = [tweet for tweet in tweet_list
                            if not pd.isnull(tweet['ParkID'])]
        tweet_list_notparks = [tweet for tweet in tweet_list
                               if pd.isnull(tweet['ParkID'])]
        park_tweet_count = len(tweet_list_parks)
        not_park_count = len(tweet_list_notparks)
        if park_tweet_count > 0 and not_park_count > 0:
            tweet_choice = random.choice(tweet_list_parks)
            control_choice = random.choice(tweet_list_notparks)
            park_tweet_text.append(tweet_choice['pure_text'])
            user_tweet_text.append(control_choice['pure_text'])
            time_tweet_text.append(tweet_choice['control_text'])
            park_list.append(tweet_choice['Park_Name'])
    return park_tweet_text, user_tweet_text, time_tweet_text, park_list


def get_time_control_text(park_user_tweets):
    """
    Take a list of lists (tweets by user) and assigns a random control tweet based on timestamp and a random control tweet from same user. Returns a list of tweets.
    Each item in return list has in-park tweet text, control tweet tet, park name, nimestamp.
    Args:
        park_user_tweets (list]): [description]

    Returns:
        [list]: [List of park tweets]
    """     
    park_tweet_text = []
    control_tweet_text = []
    park_list = []
    for user, tweet_list in park_user_tweets.items():
        tweet_count = len(tweet_list)
        tweet_list_parks = [tweet for tweet in tweet_list
                            if not pd.isnull(tweet['ParkID'])]
        park_tweet_count = len(tweet_list_parks)
        not_park_count = tweet_count-park_tweet_count
        if park_tweet_count > 0 and not_park_count > 0:
            tweet_choice = random.choice(tweet_list_parks)
            park_tweet_text.append(tweet_choice['pure_text'])
            control_tweet_text.append(tweet_choice['control_text'])
            park_list.append(tweet_choice['Park_Name'])
    return park_tweet_text, control_tweet_text, park_list


def get_user_control_text(park_user_tweets):
    park_tweet_text = []
    control_tweet_text = []
    park_list = []
    for user, tweet_list in park_user_tweets.items():
        tweet_list_parks = [tweet for tweet in tweet_list
                            if not pd.isnull(tweet['ParkID'])]
        tweet_list_notparks = [tweet for tweet in tweet_list
                               if pd.isnull(tweet['ParkID'])]
        park_tweet_count = len(tweet_list_parks)
        not_park_count = len(tweet_list_notparks)
        if park_tweet_count > 0 and not_park_count > 0:
            tweet_choice = random.choice(tweet_list_parks)
            control_choice = random.choice(tweet_list_notparks)
            park_tweet_text.append(tweet_choice['pure_text'])
            control_tweet_text.append(control_choice['pure_text'])
            park_list.append(tweet_choice['Park_Name'])
    return park_tweet_text, control_tweet_text, park_list


def getVecs(park_tweets):
    """Takes a list of tweets, joins them into string, gets the ngrams,joins the text, gets the valence and frequency vectors

    Args:
        park_tweets ([list]): List of park tweets

    Returns:
        [dict]: Dictionary of frequencvy vectors
    """
    # join lower case text for group tweets into single string
    park_text = ' '.join([tweet.lower() for tweet in park_tweets])
    # control_text = ' '.join([str(tweet['pure_text']).lower() for tweet in control_tweets])

    park_ngrams = dict(regex.get_ngrams(park_text,path='../src/func/ngrams.bin'))
    # control_ngrams = dict(regex.get_ngrams(control_text,path='../src/func/ngrams.bin'))

    park_text = ' '.join([' '.join([k] * v) for k,v in park_ngrams.items()])
    # control_text = ' '.join([' '.join([k] * v) for k,v in control_ngrams.items()])

    lang = 'english'
    labMT,labMTvector,labMTwordList = emotionFileReader(stopval=0.0,lang=lang,returnVector=True)

    ParkValence,ParkFvec = emotion(park_text,labMT,shift=True,happsList=labMTvector)
    # ControlValence,ControlFvec = emotion(control_text,labMT,shift=True,happsList=labMTvector)

    return ParkFvec


def labmtSimpleSentiment(Fvec, stopwords):
    lang = 'english'
    labMT, labMTvector, labMTwordList = emotionFileReader(stopval=1.0,
                                                         lang=lang,
                                                         returnVector=True)
    for word in stopwords:
        try:
            pos = labMTwordList.index(word)
            Fvec[pos] = 0
            #print(word, pos)
        except ValueError:
            pass
    ## but we didn't apply a lens yet, so stop the vectors first
    Fvec = stopper(Fvec,labMTvector,labMTwordList,stopVal=1.0)
    Valence = emotionV(Fvec,labMTvector)
    return Fvec, Valence


def get_park_stopwords(park_names):
    park_stops = list(filter(None, set(park_names)))
    park_stops = ' '.join(park_stops)
    park_ngram_stopwords = dict(regex.get_ngrams(park_stops,
                                path='../src/func/ngrams.bin'))
    park_ngram_stopwords = list(park_ngram_stopwords.keys())
    ignoreWords = ["nigga", "nigger", "niggaz", "niggas"]
    for word in ignoreWords:
        park_ngram_stopwords.append(word)
    return park_ngram_stopwords


def tweets_to_ngrams(tweets):
    # join lower case text for group tweets into single string
    text = ' '.join([tweet.lower() for tweet in tweets])
    ngrams = dict(regex.get_ngrams(text, path='../src/func/ngrams.bin'))
    return ngrams


def senti(ngram_dict, stop_words):
    words = labmtgen.load_labmt_words("../data/raw/data_labmt_simple.txt")
    senti_dict = words.set_index('Word').to_dict()['Happs']
    count = 0
    total = 0
    for k, v in ngram_dict.items():
        if k in stop_words:
            continue
        try:
            sentiment = senti_dict[k]
            if sentiment >= 6.0 or sentiment <= 4.0:
                total += v*sentiment
                count += v
            else:
                continue
        except KeyError:
            pass
    return total / count


def bootstrap_sentiment(park_tweets, control_tweets, stops, sample=.8,
                        runs=100, bumps=True):
    index_list = range(len(park_tweets))
    n_tweets = int(sample*len(park_tweets))
    park_sentis = []
    control_sentis = []
    for i in range(runs):
        sample = random.sample(index_list, n_tweets)
        park_tweet_sample = [park_tweets[i] for i in sample]
        control_tweet_sample = [control_tweets[i] for i in sample]

        park_ngrams = tweets_to_ngrams(park_tweet_sample)
        control_ngrams = tweets_to_ngrams(control_tweet_sample)

        stops = [x.lower() for x in dict(regex.get_ngrams(' '.join(stops),
                path='../src/func/ngrams.bin')).keys()]
        park_sentiment = senti(park_ngrams, stops)
        control_sentiment = senti(control_ngrams, stops)
        if bumps:
            park_sentis.append(park_sentiment-control_sentiment)
        else:
            park_sentis.append(park_sentiment)
            control_sentis.append(control_sentiment)
    if bumps:
        return park_sentis
    else:
        return park_sentis, control_sentis
