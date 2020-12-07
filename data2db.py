#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0103, C0321, W0621
"""
Process data files from CSB and convert them to SQLite database
Download CSV files from
https://drive.google.com/file/d/1y0y91IW1RIDAb42jfuvNzBWx3ij_Ka2A/view?ts=5f746696
Author : isezen sezenismail@gmail.com
date: 2020-10-22

NOTES:
datetime example:
c.execute("SELECT datetime((date * 3600) + 1199145600,'unixepoch'), value FROM
           data WHERE station=1002 AND pollutant=6")
"""

import os
import math
import glob
import pickle
import sqlite3 as sq3
from timeit import default_timer as timer


def read_pkl(file):
    """ Read pickle file """
    with open(file, 'rb') as f:
        x = pickle.load(f)
    return x


def get_meta_id_list(cur):
    """ get meta table as list """
    cur.execute("SELECT id, name FROM meta")
    rows = cur.fetchall()
    return list(map(list, zip(*rows)))


def get_meta_id(meta_name, meta_list):
    """ get meta id from database """
    return [meta_list[0][meta_list[1].index(v)] if v in meta_list[1] else 0
            for v in meta_name]


def get_ids(file):
    """ Get pollutant and station ids from file name """
    bn = os.path.basename(file).split('.')[0]
    return (int(i) for i in bn.split('_'))


def split2meta(v):
    """ Split a list to values and meta """
    m = [i if isinstance(i, str) else 'ok' for i in v]
    v = [i if isinstance(i, float) else float('NaN') for i in v]
    return m, v


def progressBar(iterable, prefix='', suffix='', decimals=1, length=100,
                fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent
                                  complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    total = len(iterable)

    # Progress Bar Printing Function
    def printProgressBar(iteration):
        percent = ("{0:." + str(decimals) + "f}").format(
            100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        br = fill * filledLength + '-' * (length - filledLength)
        print(f'\r{prefix} |{br}| {percent}% {suffix}', end=printEnd)
    # Initial Call
    printProgressBar(0)
    # Update Progress Bar
    for i, item in enumerate(iterable):
        yield item
        printProgressBar(i + 1)
    # Print New Line on Complete
    print()


def get_values(path):
    """ get a row from pickles """
    index_pkl = os.path.join(path, 'index.pkl')
    pkl_files = glob.glob(os.path.join(path, '*.pkl'))
    pkl_files.remove(index_pkl)
    pkl_files.sort()
    dates = read_pkl(index_pkl)
    for file in progressBar(pkl_files, prefix='Creating Data',
                            length=50):
        v = read_pkl(file)
        pol_id, sta_id = get_ids(file)
        for i, d in zip(v, dates):
            if not isinstance(i, str):
                yield pol_id, sta_id, d, i, 0


def get_meta(path, meta_list):
    """ get a row from pickles """
    index_pkl = os.path.join(path, 'index.pkl')
    pkl_files = glob.glob(os.path.join(path, '*.pkl'))
    pkl_files.remove(index_pkl)
    pkl_files.sort()
    dates = read_pkl(index_pkl)
    for file in progressBar(pkl_files, prefix='Creating Meta',
                            length=50):
        v = read_pkl(file)
        pol_id, sta_id = get_ids(file)
        m = [i for i, v in enumerate(v) if isinstance(v, str)]
        date = [dates[i] for i in m]
        m = get_meta_id([v[i] for i in m], meta_list)
        for j, d in zip(m, date):
            yield pol_id, sta_id, d, j


if __name__ == '__main__':
    s = timer()
    db_file = 'airpy/data/airpy.db'
    with sq3.connect(db_file) as con:
        cur = con.cursor()
        rows = get_values('pkl')
        cur.executemany('INSERT INTO data VALUES(?,?,?,?,?);', rows)
        con.commit()
        cur.close()

        # cur = con.cursor()
        # rows = get_meta('pkl', get_meta_id_list(cur))
        # cur.executemany('INSERT INTO data_meta VALUES(?,?,?,?);', rows)
        # con.commit()
        # cur.close()

        elapsed = timer() - s
        # print('Completed in ', int(elapsed // 60), 'min.',
        #       int(elapsed % 60), 'sec.')
        print('Creating indices...')
        cur = con.cursor()
        cur.execute('CREATE INDEX pol_index ON data (pol, sta, date)')
        cur.execute('CREATE INDEX date_index ON data (date)')
        cur.execute('CREATE INDEX sta_index ON data (sta)')
        cur.close()

    elapsed = timer() - s
    print('Database created in ', int(elapsed // 60), 'min.',
          int(elapsed % 60), 'sec.')
