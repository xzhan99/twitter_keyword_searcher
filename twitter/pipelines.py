# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import urllib
from urllib.parse import urlsplit

import pymongo
from scrapy.exceptions import DropItem


class TwitterPipeline(object):
    def __init__(self, mongo_host, mongo_port, mongo_db, mongo_col, mongo_user, mongo_pass):
        self.mongo_host = mongo_host
        self.mongo_port = mongo_port
        self.mongo_db = mongo_db
        self.mongo_col = mongo_col
        self.mongo_user = mongo_user
        self.mongo_pass = mongo_pass
        self.client = None
        self.db = None
        self.collection = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(mongo_host=crawler.settings.get('MONGODB_HOST'),
                   mongo_port=crawler.settings.get('MONGODB_PORT'),
                   mongo_db=crawler.settings.get('MONGODB_DB'),
                   mongo_col=crawler.settings.get('MONGODB_COL'),
                   mongo_user=crawler.settings.get('MONGODB_USER'),
                   mongo_pass=crawler.settings.get('MONGODB_PASS'),
                   )

    def open_spider(self, spider):
        username = urllib.parse.quote_plus(self.mongo_user)
        password = urllib.parse.quote_plus(self.mongo_pass)
        if username == '' and password == '':
            url = 'mongodb://%s:%s' % (self.mongo_host, self.mongo_port)
        else:
            url = 'mongodb://%s:%s@%s:%s' % (username, password, self.mongo_host, self.mongo_port)
        self.client = pymongo.MongoClient(url)
        self.db = self.client[self.mongo_db]
        self.collection = self.db[self.mongo_col]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        valid = True
        for data in item:
            if not data:
                valid = False
                raise DropItem("Missing {0}!".format(data))
        if valid:
            self.collection.insert_one(dict(item))
        return item
