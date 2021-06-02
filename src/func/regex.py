"""
Regular expressions for processing tweets
"""

import html
import io
import os
import re
from collections import Counter
from pathlib import Path

import pandas as pd
import requests

try:
    import cPickle as pickle
except:
    import pickle

#import .tweet_utils



def get_emojis(text, path):
    """ Parse out emojis from a given string
    :param text: a string
    :param path: path to a compiled emoji regex (emojis.bin) file
    :return: a list of re.Match objects in the given the string
    """
    if type(path) == str:
        eparser = get_ngrams_parser(path)
    else:
        eparser = path
    text = remove_whitespaces(text)
    return [m for m in re.finditer(eparser, text)]


def is_emoji(string, n_emoji, emoji_pattern):
    """Return True if get_emojis() detects emoji. Also check if number of emoji exceeds threshold, and if there are
    non-emoji characters.
    :param string: string to check for emojis
    :param emoji_pattern: emoji pattern
    :param emoji_bin: compiled regex pattern

    """
    try:
        string = string.replace(' ', '')
        regex_res = emoji_pattern.findall(string)
        return len(regex_res) == n_emoji and not len(emoji_pattern.sub('', string)) > 0
    except (TypeError, AttributeError):
        return False


def ngram_emoji_zipf(df, ngram, emoji_pattern):
    """
    Subset dataframe with just emojis of length ngram
    :param df: dataframe with 'ngram' column
    :param ngram: int order of ngram
    :param emoji_pattern:
    :return:
    """

    index = df.apply(lambda x: is_emoji(x['ngram'], ngram, emoji_pattern), axis=1)
    return df[index]


def tarball_to_emoji_tarball(
        tarball_name: str,
        outpath: Path,
        ngram_count: int,
        files_contain=['.tsv'],
        verbose=False
):
    """
    :param tarball_name: name of tarball file
    :type tarball_name: str
    :param outpath: where to save the emoji Zipf
    :type outpath: Path
    :param ngram_count: order of ngram
    :type ngram_count: int
    :param files_contain: consider files that contain strings in list (default to .tsv)
    :type files_contain: list
    :param verbose: verbose tarball read
    :type verbose: bool
    :return: None
    :rtype: None
    """

    parser = get_ngrams_parser('../emojis.bin')

    testargs = {'ngram': ngram_count, 'emoji_pattern': parser}  # kwargs for ngram_emoji_zipf func

    temp_dict = utils.read_tarball_multi(
        tarball_name,
        files_contain,
        {'compression': 'gzip', 'encoding': 'utf-8', 'sep': '\t', },
        pd.read_csv,
        ngram_emoji_zipf,
        testargs,
        verbose
    )

    out_dir = Path(outpath)

    for key, val in temp_dict.items():
        date = utils.regex_file_dates(key)
        utils.make_save_locs(out_dir, date)
        val.to_csv(out_dir / date / key.split('/')[-1], sep='\t', compression='gzip')

    utils.compress_dir(out_dir / date)


def get_ngrams(text, path, n=1):
    """ Parse out ngrams from a given string
    :param text: a string
    :param path: path to a compiled ngrams regex (ngrams.bin) file
    :param n: degree of ngrams to parse out
    :return: a Counter object of ngrams in the given string
    """
    nparser = get_ngrams_parser(path)
    text = remove_whitespaces(text)
    return ngrams(text, nparser, n)


def update_parsers(savedir):
    """ Save a regular expression that matches emojis & ngrams
    :param savedir: path to save parsers
    :return: a compiled regex
    """
    print('Compiling emoji & Ngrams parser...')
    codes = download_emojis()
    eparser = compose_emoji_regex(codes)
    with open(os.path.join(savedir, 'emojis.bin'), "wb") as f:
        parser = re.compile(eparser)
        pickle.dump(parser, f)

    nparser = compose_ngrams_regex(eparser)
    with open(os.path.join(savedir, 'ngrams.bin'), "wb") as f:
        parser = re.compile(nparser, flags=re.UNICODE)
        pickle.dump(parser, f)


def get_tlid_basic():
    """
    The regex for just text (no emojis) from the tlid project. Captures links, dates, decimal numbers, currencies
    :return: raw string (to be fed into re package)
    """
    pattern = r"((&\S+;)"
    pattern += r"|(https?:\/\/\w+\.\S+)"
    pattern += r"|((?:\b|[@\#\$\£\¥\¢]|[\u20a0-\u20cf])[\u20a0-\u20cf\$\£\¥\¢\w\@\.\#\‘\’\'\&\:\,\]\*\-\/\[\=]+([\'\']|\b))"
    pattern += r"|([\-\.]+)"
    pattern += r' + )'
    return pattern


def html2unicode(code):
    """ Converts HTML entities to unicode ('&amp;' => '&') """
    return html.unescape(code)


def hex2unicode(code):
    """ Converts hex-values to unicode ('1F609' => '😉') """
    code = [r'\U' + x.zfill(8) for x in code.split()]
    code = ''.join(code)
    return bytes(code, 'ascii').decode('unicode-escape')


def remove_whitespaces(text):
    """ Strip out extra whitespaces
    :param text: a string
    :return: cleaned text
    """
    text = re.sub(r'\s\s+', ' ', text)
    text = re.sub(r'\n|\t', ' ', text)
    text = re.sub(u'\u20e3|\ufe0f|\u2800|\u200b|\u200c|\u200d|<200b>|<200c>|<200d>', '', text)
    text = text.strip()
    return html2unicode(text)


def filter_text(text):
    """ Filter out retweet-prefix, urls, html-codes, hashtags, handles, and extra whitespaces
    :param text: a string
    :return: cleaned text
    """
    return re.sub(
        r'(RT @\S+:)|(RT)|(https?:\S+)|(&\S+;)|(@\S+)|(#\S+)', '',
        text
    )


def ngram_parser(text, ngram_parser):
    """ Parse out N-grams using a custom regex
    :param: text: a string object
    :param ngram_parser: a compiled regex expression to extract one-grams
    :return a list of 1-grams
    """
    # take care of a few edge cases
    text = re.sub(r'(([\-\.]{2,})|(\'\'))', r' \1 ', text)
    return [x[0] for x in ngram_parser.findall(text) if x[0] != '']


def ngrams(s, parser, n=1):
    """ Concatenate tokens into ngrams
    :param s: a string object
    :param parser: a compiled regex expression to extract one-grams
    :param n: the degree of the ngrams
    :return: a Counter object of n-grams
    """
    tokens = ngram_parser(s, parser)

    if len(tokens) == 0:
        return None
    else:
        ngrams = zip(*[tokens[i:] for i in range(n)])
        return Counter([" ".join(ngram) for ngram in ngrams])


def compose_emoji_regex(codes):
    """ Compose a regex expression to parse out emojis
    :param codes: [
        a list of single-based emojis (unicodes),
        a list of group-based emojis (unicodes, skin-tones, flags, etc.)
    ]
    :return: a regular expression that matches emojis
    """

    def formater(u):
        if '..' in u:
            start, end = u.split('..')
            return '[' + re.escape(hex2unicode(start)) + '-' + re.escape(hex2unicode(end)) + ']'
        else:
            return re.escape(hex2unicode(u))

    singles, modifiers = '', ''
    for e in sorted(codes, reverse=True):
        singles += f'|{formater(e)}' if singles != '' else formater(e)

    # skin-tones, hair-types
    modifiers = f'{formater("1F3FB..1F3FF")}?{formater("200D")}?{formater("1F9B0..1F9B3")}?'

    # regional-indicators
    flags = f'{formater("1F1E6..1F1FF")}{{2}}'

    return f'({flags})|({singles})({modifiers})'


def compose_ngrams_regex(emoji_regex):
    """ Compose a regex expression to parse out Ngrams
    :param emoji_regex: a regular expression that matches emojis
    :return: a compiled regular expression that matches ngrams
    """
    pattern = '(' + emoji_regex
    pattern += r"|(&\S+;)"
    pattern += r"|(https?:\/\/\w+\.\S+)"
    pattern += r"|((?:\b|[@\#\$\£\¥\¢]|[\u20a0-\u20cf])[\u20a0-\u20cf\$\£\¥\¢\w\@\.\#\‘\’\'\&\:\,\]\*\-\/\[\=]+([\'\']|\b))"
    pattern += r"|([\-\.]+)"
    pattern += r"|(\S)" + ')'
    return pattern


def get_emojis_parser(path):
    """ Load a regular expression that matches emojis
    :param path: path to a (.bin) file
    :return: a compiled regex
    """
    with open(path, "rb") as f:
        return pickle.load(f)


def get_ngrams_parser(path):
    """ Load a regular expression that matches ngrams
    :param path: path to a (.bin) file
    :return: a compiled regex
    """
    with open(path, "rb") as f:
        return pickle.load(f)


def download_emojis(version='12.0'):
    """ Extract a list of emojis and names from the official unicode
        website: http://www.unicode.org/emoji
    :param version: target version to download
    :return a list of emojis
    """
    df = pd.read_csv(
        io.StringIO(
            requests.get(
                f'https://www.unicode.org/Public/emoji/{version}/emoji-data.txt'
            ).content.decode('utf-8')
        ),
        usecols=[0, 1],
        names=['code', 'dtype'],
        sep=';', comment='#')

    df['code'] = df['code'].str.strip(r' +')
    df['dtype'] = df['dtype'].str.strip(r' +')

    df = df.loc[df['code'] >= hex(0x2000)]
    df = df.drop_duplicates(subset='code', keep='first')
    emojis = df.loc[df['dtype'].isin([
        'Emoji', 'Emoji_Modifier_Base', 'Emoji_Presentation', 'Extended_Pictographic'
    ])]
    return emojis.code.values
