"""
汎用的な関数群
"""

import json


def response(code):
    """ レスポンスコードをメッセージのリストに変換して返す """
    return {
        400: ['400', 'Bad Request'],
        403: ['403', 'Forbidden'],
        404: ['404', 'Not Found'],
        405: ['405', 'Method Not Allowed'],
    }[code]


def output_json(obj, filename='backup.json'):
    """ オブジェクトをjsonファイルで出力 """
    with open(filename, 'w') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
