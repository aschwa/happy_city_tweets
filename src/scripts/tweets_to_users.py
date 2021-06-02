#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from pathlib import Path
from src.scripts.process_tweets import user_control_split, load_tweets


def save_tweets(tweets, path):
    with open(path, 'w') as fout:
        json.dump(tweets, fout, sort_keys=True, default=str)


if __name__ == "__main__":
    in_dir = Path("../../data/processed/tweets/")
    out_dir = Path("../../data/processed/park_user_tweets_0530/")
    hashtag_file = Path("hashtags.json")
    with open(hashtag_file, 'r') as fp:
        hashtags = json.load(fp)
    print("Ignoring tweets with hashtags {}".format(hashtags))
    for city in in_dir.glob("*.json"):
        tweets = load_tweets(city)
        print("Loaded {} tweets for {}".format(len(tweets), city.name))
        park_tweets_by_user = user_control_split(tweets, hashtags)
        out_file = out_dir / city.name
        save_tweets(park_tweets_by_user, out_file)
        print(city.stem, "users saved: ", len(park_tweets_by_user))
