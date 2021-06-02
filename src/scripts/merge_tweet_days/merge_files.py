#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import argparse
from pathlib import Path
from src.func import geo_utils


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("tweet_directory",
                        help='tweet file directory',
                        type=Path)
    args = parser.parse_args()
    return args


def save_tweets(tweets, path):
    with open(path, 'w') as fout:
        json.dump(tweets, fout, sort_keys=True, default=str)


if __name__ == "__main__":
    args = parse_args()
    # Load path to tweet files
    raw_dir = Path("../../data/raw/tweets")
    tweet_dir = raw_dir / args.tweet_directory
    all_tweets = geo_utils.merge_tweets(tweet_dir)
    # Load tweets from json file, get park tweets and label
    all_tweet_path = (tweet_dir.parent / tweet_dir.stem).with_suffix(".json")
    save_tweets(all_tweets, all_tweet_path)
