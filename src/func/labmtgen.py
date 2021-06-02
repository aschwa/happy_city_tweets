# Parsing tweets into 15 minute {word:count} dicts
import json as json
import codecs
import datetime
import re
import numpy
import sys
import pickle

from collections import Counter
import argparse
from pathlib import Path
import time
from datetime import datetime, timedelta
import os
import gzip
import tarfile
import shutil
from multiprocessing import Pool
import pandas as pd
import glob

import zlib
#import utils


def make_args():
    description = "Extract labmt vectors from txt zipf files."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-i',
                        '--inputdir',
                        help='path to input directory of pydicts',
                        required=True,
                        type=valid_path)
    parser.add_argument('-o',
                        '--outdir',
                        help='path to output directory (where .txts are saved)',
                        required=True,
                        type=valid_path)
    parser.add_argument('-s',
                        '--startdate',
                        help='start date for this run',
                        required=False,
                        type=valid_date)
    parser.add_argument('-e',
                        '--enddate',
                        help='end date for this run',
                        required=False,
                        type=valid_date)
    parser.add_argument('-l',
                        '--language',
                        help='twitter language code to pull from. all if None',
                        default='',
                        required=False,
                        type=str)
    parser.add_argument('--labmtloc',
                        help='list of dates separated by underscores',
                        required=False,
                        default=Path(sys.argv[0]).resolve().parent / '../data/labmt_simple.txt',
                        type=str)
    parser.add_argument('--datelist',
                        help='list of dates separated by underscores',
                        required=False,
                        type=str_check)
    return parser.parse_args()


def valid_path(p):
    return Path(p)


def str_check(s):
    if s == 'nad':
        return None
    else:
        return s


def valid_date(d):
    """Convert to valid date and return None if str input is nad"""

    if d == 'nad':
        return None
    try:
        return datetime.strptime(d, "%Y-%m-%d")

    except ValueError:
        msg = "Invalid date format in provided input: '{}'.".format(d)

        raise argparse.ArgumentTypeError(msg)


def arg_to_parserfunc(args):
    """Args to parser function.
    """
    if args.tweetparser == 'originalhed':
        return parsers.text_to_count_dict
    elif args.tweetparser == 'removecjk':
        return parsers.remove_CJK_parser


def get_dates(start, end):
    """ Get the dates for the file path, from the [start, end] range passed

    Args:
        start: datetime object for start date
        end: datetime object for end date

    Returns:
        files: string dates
    """

    files = []

    while start <= end:
        p = start
        start += timedelta(days=1)
        files.append(p)

    return sorted(files)


def get_file_names(dir_path, day):
    """ return the file path for the unique file structure around the .py3dicts

    Args:
        dir_path: posixpath
        day: the day of the dict being selected

    """

    this_day = dir_path / day

    print(f'loading files from {this_day}')

    return [x for x in this_day.iterdir()]


def save_labmt_vector(labmt_vector, outputdir, save_path):
    """ Save the labmt vector to csv file.

    """

    f = open(Path(outputdir) / save_path, "w")
    f.write("\n".join(list(map(lambda x: "{0:.7f}".format(x), labmt_vector))))

    return


def load_zipf(inpath, language, labmtlist, date, subfolder='1grams'):
    """ Load zipf files from txt.

    :param inpath: path to the zipf file
    :param language: language code for the zipf of interest
    :return: dict of lowercase word2count
    """

    print(glob.glob(f'{inpath}/{date}*'))
    tarballname = glob.glob(f'{inpath}/{date}*')[0]

    zipf = utils.read_tarball(tarballname,
                              f'/{language}_{date}',
                              {'compression': 'gzip',
                               'encoding': 'utf-8',
                               'sep': '\t'
                               }
                              )

    zipf = zipf[zipf.ngram.str.lower().isin(labmtlist.Word.values)]

    zipf.set_index('ngram', inplace=True)

    print(zipf['count'].head())

    zipf_dict = zipf['count'].to_dict()

    lowercase_dict = {str(key).lower(): 0 for key in zipf_dict.keys()}

    for key, val in zipf_dict.items():
        lowercase_dict[str(key).lower()] += val

    return lowercase_dict
    #return zipf_dict


def load_labmt_words(filepath='../data/labmt_simple.txt'):
    """ Load the labmt words in order

    """

    simplelabmt = pd.read_csv(filepath, sep=' ')
    simplelabmt.columns = ['Word', 'Happs']

    return simplelabmt


def dict_to_vec(dict_obj, labmt_words):
    """ dict to labmt word vector for use in hedonometer

    :param labmt_words: ordered vector of strings for labmt
    :param dict_obj: dict of word2count
    :return: np array of labmt counts

    """
    # return np.array([[dict_obj.get(word,0)] for word in labmt_words])

    # print(list(dict_obj.keys())[:10])
    return [dict_obj.get(word, 0) for word in labmt_words]


def main():
    args = make_args()
    print('args made')

    compress_output = True

    # if we're running a date range
    if args.enddate is not None:
        dates_for_files = get_dates(args.startdate, args.enddate)

    # if we're running a date list (no-contiguous)
    elif args.datelist:
        dates_for_files = [valid_date(x) for x in args.datelist.split('_')]

    # single day
    elif args.startdate:
        dates_for_files = [args.startdate]

    else:
        print(f'Error: No dates provided.')
        return

    print(f'Dates for files{dates_for_files}')

    labmtlist = load_labmt_words(args.labmtloc)

    for date in dates_for_files:

        try:
            count_dict = load_zipf(args.inputdir, args.language, labmtlist, date.date())

            print(count_dict)

            save_labmt_vector(dict_to_vec(count_dict, labmtlist.Word.values), args.outdir, str(date.date()) + '.txt')

        except FileNotFoundError as e:
            print(f'File not found for {date} moving to next date. Specific error {e}')
            continue

    return


if __name__ == '__main__':
    main()
