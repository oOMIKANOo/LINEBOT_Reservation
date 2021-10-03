from tinydb import TinyDB, Query
from time import time


class ChatSession:
    UserId = ""
    Created = ""
    CacheMinute = ""

    def __init__(self, UserId, CacheMinute=15, *args, **kwargs):
        self.UserId = UserId
        self.CacheMinute = CacheMinute * 60

    def __getitem__(self, key):
        db = TinyDB("cache.json")
        query = Query()

        # 該当データを拾う
        item = db.search(query.UserId == self.UserId)

        # データの有無を検証
        if item:
            item = item[0]
            self.Created = item["Created"]
            # TTL
            if time() - self.Created < self.CacheMinute:
                try:
                    return item[key]
                except KeyError:
                    return ""
            else:
                # 有効期限切れ
                db.remove(query.UserId == self.UserId)
                return ""
        else:
            return ""

    def __setitem__(self, key, val):
        db = TinyDB("cache.json")
        query = Query()

        # 該当データを拾う
        item = db.search(query.UserId == self.UserId)

        # データの有無を検証
        if item:
            item = item[0]
            self.Created = item["Created"]
            if time() - self.Created < self.CacheMinute:
                db.update({key: val}, query.UserId == self.UserId)
        else:
            db.insert({"UserId": self.UserId, "Created": time()})
            db.update({key: val}, query.UserId == self.UserId)
