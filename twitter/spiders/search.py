# -*- coding: utf-8 -*-
import scrapy


class SearchSpider(scrapy.Spider):
    name = 'search'
    allowed_domains = ['twitter.com']
    start_urls = ['http://twitter.com/']

    def parse(self, response):
        pass
