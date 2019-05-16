"""
db(redis)の操作に関する関数群
botとコマンドラインの双方で利用できる
"""

import argparse
import os
import re
import redis
from functools import reduce
from operator import and_
from tqdm import tqdm
from utils import output_json

r = redis.from_url(os.getenv('REDIS_URL'), decode_responses=True)


def normalize():
    """
    DB内のデータの形式や紐付けを自動で整理する
    ・データが対になっているか検証&修復
    ・twitterURLのhttpをhttpsに置換
    ・twitterのURLにアカウントIDを紐付ける
    """
    for key in sorted(r.keys()):
        if r.type(key) == 'set':
            for value in r.smembers(key):
                if key in r.smembers(value):
                    print(f'PAIRED {key} AND {value}')
                else:
                    r.sadd(value, key)
                    print(f'RESTORED {key} IN {value}')
        else:
            print('IS STRING {} IN {}'.format(r.get(key), key))
    for url in r.keys('http://twitter.com/*'):
        for value in r.smembers(url):
            r.srem(value, url)
            sadd_pair(value, url.replace('http', 'https'))
            print(f'REPLACE w/ HTTPS {url} in {value}')
        r.delete(url)
        print(f'REPLACE w/ HTTPS {url}')
    pattern = re.compile(
        r'(https?:\/\/twitter\.com\/)([-_.!~*\'()a-zA-Z0-9;\/?:\@&=+\$,%#]+)')
    for value in sorted(r.smembers('twitter.com')):
        match = pattern.match(value)
        if match:
            userid = match.group(2).split('/')[0]
            sadd_pair(value, userid)
            print(value, userid)


def sadd_pair(a, b):
    """
    データが対になるように記録
    データの記録には必ずこの関数を使う
    """
    r.sadd(a, b)
    r.sadd(b, a)


def get_intersection(args):
    """ 指定した引数リストをキーにしたデータの積集合を返す """
    return reduce(
        and_,
        (r.smembers(key) for arg in args for key in r.keys(arg))
        )


def set_values(key, values):
    """ valuesを指定したkeyに記録 """
    for value in values:
        sadd_pair(key, value)
        print(f'RECORDED {key} & {value}')


def smembers(key):
    """ r.smembersを取得 """
    if r.exists(key):
        return sorted(r.smembers(key))
    return []


def record_urls(text):
    """ urlを検出して記録する """
    # refs https://www.ipentec.com/document/regularexpression-url-detect
    pattern = r'https?:\/\/[-_.!~*\'()a-zA-Z0-9;\/?:\@&=+\$,%#]+'
    urls = re.findall(pattern, text)
    for url in urls:
        domain = url.split('://')[1].split('/')[0]
        sadd_pair('url', url)
        sadd_pair(domain, url)
        sadd_pair('domain', domain)
    return urls


def delete(args):
    """ 引数に指定したデータを削除 """
    for arg in args:
        for key in r.keys(arg):
            for value in r.smembers(key):
                if r.exists(value):
                    r.srem(value, key)
                    print(f'DELETED {key} in {value}')
                else:
                    print(f'FORBIDDEN {key} in {value}')
            r.delete(key)
            print(f'DELETED {key}')


def backup():
    """ 全データをファイルに出力 """
    output_json({key: get4json(key) for key in tqdm(sorted(r.keys()))})


def get4json(key):
    """ データを取得しjson用に正規化して返す """
    data = {
        'string': r.get,
        'set': r.smembers,
        }[r.type(key)](key)
    return data if type(data) != set else sorted(list(data))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--set', action='store_true')
    parser.add_argument('-g', '--get', nargs='*')
    parser.add_argument('-k', '--key', nargs=1)
    parser.add_argument('-v', '--value', nargs='*')
    parser.add_argument('-d', '--delete', nargs='*')
    parser.add_argument('-n', '--normalize', action='store_true')
    parser.add_argument('-b', '--backup', action='store_true')
    args = parser.parse_args()
    if args.set and args.key and args.value:
        set_values(args.key[0], args.value)
    if args.get:
        [print(d) for d in sorted(get_intersection(args.get))]
    if args.delete:
        delete(args.delete)
    if args.normalize:
        normalize()
    if args.backup:
        backup()
