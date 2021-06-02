import gzip
import json as json
import os
import tarfile
import shutil
import time
from os.path import basename
import pandas as pd
import re

"""Utility functions for working with Tweet data, namely CSL Decahose format."""


def find_rt_text(text):
    """
    regex for RT pattern return the RT enrichment
    :param text: text from tweet
    :return: RT enrichment from text
    """

    regex = re.compile(r'RT \@\S+\:')

    try:
        return regex.findall(text)[0]
    except (TypeError, IndexError):
        return ''


def rt_enrich(text, handle):
    return f"RT @{handle}: " + text


def get_text(tweet, enrich_rt=False, no_text=0, failed_parse=0):
    """ Take a tweet object and return the body/text attributes for all formats in decahose.
            Tweets, RTs, and RTs with comments are accounted for.

    Usage note: RTs are enriched when tags are missing from text fields. RTs and original
            tweets are returned in the same fashion, with the second return item being None.
            RTs with comments return the comment first and RT'd body is returned as the second item.

    :param tweet: dict object of parser tweet
    :param word_dict: dictionary of word2count
    :param no_text: int for counting text presence
    :param failed_parse: int for counting parsing issues
    :param enrich_rt: if true enrich (prepend) RTs from long objects with "RT <username>:" (for consistency with body)
    :return: <body>, None for RTs / Tweets and <comment>, <RT body> for RT w/ comments

    """
    rt_text = None

    if 'text' in tweet:  # old format
        try:  # get RT content if RT with comment (post April 2015)
            rt_text = tweet['retweeted_status']['quoted_status']['text']
        except KeyError:
            pass

        try:
            return tweet['text'], rt_text
        except KeyError:
            failed_parse += 1

    elif 'body' in tweet:  # from GNIP / new format
        try:  # get RT content if RT with comment
            try:  # look for long retweets
                if enrich_rt:  # grab user name from quoted status
                    rt_text = rt_enrich(
                        tweet['twitter_quoted_status']['long_object']['body'],
                        tweet['twitter_quoted_status']['actor']['preferredUsername']
                    )
                else:
                    rt_text = tweet['twitter_quoted_status']['long_object']['body']
            except KeyError:
                if enrich_rt:  # grab user name from quoted status
                    rt_text = rt_enrich(
                        tweet['twitter_quoted_status']['body'],
                        tweet['twitter_quoted_status']['actor']['preferredUsername']
                    )
                else:
                    rt_text = tweet['twitter_quoted_status']['body']
        except KeyError:
            pass

        try:  # body from short tweets, load this first for enrichment purposes
            body = tweet['body']
        except KeyError as e:
            failed_parse += 1
            return None, None

        try:  # look for long retweets
            return find_rt_text(body) + tweet['object']['long_object']['body'], rt_text
        except KeyError:
            pass

        try:  # look for tweets with characters > 140
            return find_rt_text(body) + tweet['long_object']['body'], rt_text
        except KeyError:
            pass

        return body, rt_text  # body is longest value to return
    else:
        no_text += 1

    return None, None


def is_retweet(tweet):
    """ Check tweet type (tweet/retweet) from a tweet object
    :param tweet: JSON object
    :return: True/False
    """
    try:  # for new tweets format (GNIP)
        if str(tweet['verb']) == 'share':
            return True
    except KeyError:
        try:
            if str(tweet['body']).startswith('RT'):
                return True
        except KeyError:
            pass

        try:
            if str(tweet['text']).startswith('RT'):
                return True
        except KeyError:
            pass

    return False


def get_tweet_id(tweet):
    """ Get id from a tweet object
    :param tweet: JSON object
    :return: (new_id, None) for RTs/Tweets and (new_id, ref_id) for RT w/ comments
    """
    new_id, ref_id = None, None

    try:
        new_id = tweet['id']
    except KeyError:
        pass

    try:  # old retweets
        ref_id = tweet['retweeted_status']['quoted_status']['id']
    except KeyError:
        pass

    try:  # GNIP format
        ref_id = tweet['object']['twitter_quoted_status']['id']
    except KeyError:
        pass

    return new_id, ref_id


def get_user_id(tweet):
    """ Get user's id from a tweet object
    :param tweet: JSON object
    :return: (new_id, None) for RTs/Tweets and (new_id, ref_id) for RT w/ comments
    """
    new_id, ref_id = None, None

    try:
        new_id = tweet['actor']['id']
    except KeyError as e:
        pass

    try:
        new_id = tweet['user']['id']
    except KeyError as e:
        pass

    try:  # old retweets
        ref_id = tweet['retweeted_status']['quoted_status']['user']['id']
    except KeyError:
        pass

    try:  # GNIP format
        ref_id = tweet['object']['twitter_quoted_status']['actor']['id']
    except KeyError:
        pass

    return new_id, ref_id


def get_lang(tweet):
    """ Get language label from a tweet object
    :param tweet: JSON object
    :return: (new_lang, None) for RTs/Tweets and (new_lang, ref_lang) for RT w/ comments
    """
    try:
        new_lang = tweet['twitter_lang']
    except KeyError as e:
        try:
            new_lang = tweet['lang']
        except KeyError as e:
            new_lang = 'unknown'

    try:  # old retweets
        ref_lang = tweet['retweeted_status']['quoted_status']['twitter_lang']
    except KeyError:
        try:  # GNIP format
            ref_lang = tweet['object']['twitter_quoted_status']['lang']
        except KeyError:
            ref_lang = 'unknown'

    return new_lang, ref_lang


def read_tarball(tarball_name, filename, kwargs={}, open_func=pd.read_csv):
    """ Read file(s) from tarball
    :param tarball_name: path to tarball
    :param filename: name of file in tarball
    :param open_func: the function to open filewith
    :return: file of interest
    """

    print(f'Loading from tarball{tarball_name}')
    t0 = time.time()

    with tarfile.open(tarball_name) as tarball_obj:
        # print(tarball_obj.getnames())
        dict_files = [x for x in tarball_obj.getnames() if filename in x]
        # print(f'FOI : {dict_files}')

        if len(dict_files) > 1:
            print('Warning: more that one file meets criteria in tarball')

        extracted = open_func(tarball_obj.extractfile(dict_files[0]), **kwargs)

    print(f'Loaded {dict_files[0]} ~ {time.time() - t0:.2f} secs.')
    return extracted


def read_tarball_multi(tarball_name,
                       filenames,
                       kwargs={},
                       open_func=pd.read_csv,
                       stream_func=None,
                       sfargs={},
                       verbose=False):
    """ Read file(s) from tarball AND return multiple objects in filename2object dict
    :param tarball_name: path to tarball
    :param filenames: list of filenames in tarball (conducting basic pythong string contains check)
    :param open_func: the function to open file with
    :param stream_func: function to call while streaming from within tarball
    :param sfargs: kwargs for stream function
    :param verbose: print progress in read tarball
    :return: filename2output dict
    """

    t0 = time.time()

    filename2output = {}

    with tarfile.open(tarball_name) as tarball_obj:

        if verbose: print('First 10 files', list(tarball_obj.getnames())[:10])
        if isinstance(filenames, list):  # if we have a list of criteria
            dict_files = [[x for x in tarball_obj.getnames() if check in x] for check in filenames]
            dict_files = set([x for y in dict_files for x in y])
        else:
            dict_files = [x for x in tarball_obj.getnames() if filenames in x]

        if len(dict_files) < 1:
            print('Warning: less than one file meets criteria in tarball')

        for filename in dict_files:

            if verbose: t_loop = time.time(); print(f'Starting {filename}')

            extracted = open_func(tarball_obj.extractfile(filename), **kwargs)

            if stream_func:  # if we want to perform action within stream
                filename2output.update({filename: stream_func(extracted, **sfargs)})
            else:
                filename2output.update({filename: extracted})

            if verbose:
                print(f'Read {filename} in {time.time() - t_loop} seconds.')

    print(f'Loaded from tarball in {time.time() - t0} secs.')
    return filename2output


def read_tweet_metadata(tweet_object, att_to_check, custom_list=None):
    """read tweet metadata from multiple formats
    :param tweet_object: json tweet object
    :param att_to_check: key for the predefined dictionary
    :return: attribute value
    ----
    Predefined attributes
    - retweets:
       atts_to_check : ['retweetCount','retweet_count']~
    - favorites:
       atts_to_check : ['favoritesCount','favorite_count']

    ----
    """

    meta_data_dict = {'retweets':
                          ['retweetCount',
                           ['retweeted_status', 'retweet_count'],
                           'retweet_count'
                           ],
                      'favorites':
                          [['object', 'favoritesCount'],
                           ['object', 'favorite_count'],
                           ['retweeted_status', 'favorite_count'],
                           'favoritesCount']}

    for att in meta_data_dict[att_to_check]:
        if isinstance(att, list):  # if attribute key is nested
            try:
                read = tweet_object[att[0]]
                for a in att[1:]:
                    read = read[a]
                return read
            except KeyError:
                pass

        else:  # else single attribute
            try:
                return tweet_object[att]
            except KeyError:
                pass

    return


def tweet_id_to_timestamp(theid):
    """ Get millisecond creation time from twitter IDs

    :param theid: int id from tweet object
    :return: timestamp of object creation

    ----
    !!Only works for tweets authored after 2010-06-01!!
    ----

    """

    return ((theid >> 22) + 1288834974657) / 1000


def write_tweets_out(tweet_list, outfile):
    """ Write tweet list to a line seperated json .gz in the same format as the decahose.

    """

    with gzip.open(outfile, 'wb') as f:
        for tweet in tweet_list:
            f.write(json.dumps(tweet).encode('utf8'))
            f.write('\n'.encode('utf8'))

    return


def regex_file_dates(filename, regex_pattern=r'(\d{4}\-\d{1,2}\-\d{1,2})'):
    """
    Extract datetime in YYYY-MM-DD format

    :param filename: string to run regex on
    :param regex: regex for date
    :return: datetime string
    """
    try:
        return re.findall(regex_pattern, basename(os.path.splitext(filename)[0]))[0]
    except IndexError:
        return None


def compress_dir(outpath, deleteold=True):
    """ Compress the directory of outpaths

    """

    outpath = str(outpath)

    file = outpath.split('/')[-1]
    # print(f'Compressing from these files: {os.listdir(outpath)}')
    # print('compressing directory: {}'.format(outpath))

    t0 = time.time()

    with tarfile.open('{}.tar.gz'.format(outpath), 'w:gz') as tar:
        tar.add(outpath, arcname=file)
    if deleteold:
        shutil.rmtree(outpath)

    print('compressed directory in {} seconds'.format(time.time() - t0))

    return


def make_save_locs(outputdir, date):
    """ Make save folders for various outputs. assumes ~/outputdir/date/files format
    """

    if os.path.exists(outputdir / date):
        return

    os.mkdir(outputdir / date)

    return


def main():
    print('exiting')
    return


if __name__ == '__main__':
    main()
