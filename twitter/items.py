# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class TwitterItem(scrapy.Item):
    tweet_id = scrapy.Field()
    tweet_info = scrapy.Field()
    keyword = scrapy.Field()
    api_url = scrapy.Field()
    crawl_date = scrapy.Field()
