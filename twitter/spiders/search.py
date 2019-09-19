# -*- coding: utf-8 -*-
import calendar
import copy
import json
import logging
import time
from datetime import datetime
from urllib.parse import urlencode

import scrapy
from scrapy import Request

from twitter.items import TwitterItem

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def extract_contents(tweet):
    tweet_info = {
        'id': tweet['id'],
        'full_text': tweet['full_text'],
        'created_at': datetime.strptime(tweet['created_at'], '%a %b %d %X %z %Y').strftime('%Y-%m-%dT%H:%M:%S.000Z'),
        'hashtags': [],
        'media': [],
        'external_urls': [],
        'source': tweet['source'],
        'user_id': tweet['user_id'],
        'geo': tweet['geo'],
        'place': tweet['place'],
        'is_quote_status': tweet['is_quote_status'],
        'retweet_count': tweet['retweet_count'],
        'reply_count': tweet['reply_count'],
        'lang': tweet['lang']
    }
    entities = tweet['entities']
    for tag in entities.get('hashtags', []):
        tweet_info['hashtags'].append(tag['text'])
    for media in entities.get('media', []):
        tweet_info['media'].append({'type': media['type'], 'url': media['media_url']})
    for external_url in entities.get('urls', []):
        tweet_info['external_urls'].append(external_url['expanded_url'])
    return tweet_info


def form_search_key(keyword, lang, year, month):
    last_day = calendar.monthrange(year, month)[1]
    key = '"%s" lang:%s until:%d-%s-%s since:%d-%s-01' % (
        keyword, lang, year, str(month).zfill(2), str(last_day).zfill(2), year, str(month).zfill(2))
    return key


class SearchSpider(scrapy.Spider):
    name = 'search'
    # allowed_domains = ['*']
    start_urls = ['https://www.google.com']

    headers = {
        'Host': 'api.twitter.com',
        'Connection': 'keep-alive',
        'x-twitter-client-language': 'en',
        'x-csrf-token': '4982824d790f3281847d4d765c59dd64',
        'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
        'Accept-Language': 'en,zh-CN;q=0.9,zh;q=0.8',
    }
    cookies = {
        'ct0': '4982824d790f3281847d4d765c59dd64',
        'auth_token': '178af9c51ed79f67aee3e24086b21bdab7cf0b4a'
    }

    base_url = 'https://api.twitter.com/2/search/adaptive.json?'
    query_dict = {
        'include_profile_interstitial_type': [1],
        'include_blocking': [1],
        'include_blocked_by': [1],
        'include_followed_by': [1],
        'include_want_retweets': [1],
        'include_mute_edge': [1],
        'include_can_dm': [1],
        'include_can_media_tag': [1],
        'skip_status': [1],
        'cards_platform': ['Web-12'],
        'include_cards': [1],
        'include_composer_source': ['true'],
        'include_ext_alt_text': ['true'],
        'include_reply_count': [1],
        'tweet_mode': ['extended'],
        'include_entities': ['true'],
        'include_user_entities': ['true'],
        'include_ext_media_color': ['true'],
        'include_ext_media_availability': ['true'],
        'send_error_codes': ['true'],
        'q': [],
        'count': [75],
        'cursor': [],
        'query_source': ['typed_query'],
        'pc': [1],
        'spelling_corrections': [1],
    }
    search_words = ['cancer', 'diabetes', 'pneumonia', 'common cold']
    lang = 'en'
    year = 2009
    month = 1

    count = 0

    def parse(self, response):
        for keyword in self.search_words:
            new_query = copy.deepcopy(self.query_dict)
            query_key = form_search_key(keyword, self.lang, self.year, self.month)
            new_query['q'].append(query_key)
            url = self.base_url + urlencode(new_query, doseq=True)
            yield Request(url, headers=self.headers, cookies=self.cookies, meta={'keyword': query_key},
                          callback=self.parse_json_result)

    def parse_json_result(self, response):
        contents = json.loads(response.text)
        for tweet_id, tweet_content in contents['globalObjects']['tweets'].items():
            item = TwitterItem()
            item['tweet_info'] = extract_contents(tweet_content)
            item['tweet_id'] = int(tweet_id)
            item['keyword'] = response.meta['keyword']
            item['month'] = '%d-%s' % (self.year, str(self.month).zfill(2))
            item['api_url'] = response.url
            item['crawl_date'] = time.strftime('%Y-%m-%d', time.localtime(time.time()))
            self.count += 1
            yield item

        instruction = contents['timeline']['instructions'][-1]
        if 'addEntries' in instruction.keys():
            cursor = instruction['addEntries']['entries'][-1]['content']['operation']['cursor']['value']
        elif 'replaceEntry' in instruction.keys():
            cursor = instruction['replaceEntry']['entry']['content']['operation']['cursor']['value']
        else:
            logging.exception('Failed to get cursor from %s' % response.url)
            return

        if self.count > 5000:
            return
        new_query = copy.deepcopy(self.query_dict)
        new_query['q'].append(response.meta['keyword'])
        new_query['cursor'].append(cursor)
        next_url = self.base_url + urlencode(new_query, doseq=True)
        yield Request(next_url, headers=self.headers, cookies=self.cookies, meta=response.meta,
                      callback=self.parse_json_result)
