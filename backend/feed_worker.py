import os
import sys
import yql
import time
import json
import base64
import socket
import urllib
import urllib2
import hashlib
#import memcache
import traceback
import feedparser

from bson import json_util
from datetime import datetime

CWD = os.path.dirname(__file__)

path = os.path.abspath(os.path.join(CWD, '..'))
if not path in sys.path:
    sys.path.insert(1, path)
del path

from lib import params
from lib.queue_handler import QueueHandler
from lib.mongo_handler import MongoHandler


class FeedsWorker(QueueHandler):
  def __init__(self, name='feed_worker'):

    self.name = name
    try:
      QueueHandler.__init__(self, is_producer=False, queue_name='feeds_queue') # QueueHandler inits config_handler
      self.init_config()
      self.init_yql()
      self.init_db()
      self.init_url_opener()
      print 'Feeds worker %s started' % self.name
    except Exception as e:
      print 'Worker %s failed in FeedsWorker init ' % (self.name), traceback.format_exc()
      raise Exception(e)

  def init_yql(self):
    self.yql = yql.TwoLegged(params.YAHOO_API_KEY, params.YAHOO_API_SECRET)

  def init_config(self):
    self.feeds_to_refresh_collection = 'feeds_to_refresh1'
    self.max_feed_items = 50
    self.feed_timeout = 120


  def init_db(self):
    self.mongo_handler = MongoHandler()
    self.feeds_to_refresh_collection = self.mongo_handler.db[self.feeds_to_refresh_collection]



  def init_url_opener(self):
    # Use the feed_parser's URL handler. This is a hack to add a timeout to feed_parser.
    # We create an opener object with its URL Handler and add a timeout when actually downloading
    # the url. The string response is then fed to the feed_parser

    self.url_opener = urllib2.build_opener(feedparser._FeedURLHandler)


  def get_dict_from_json(self, json_str):
    return json.loads(json_str, object_hook=json_util.object_hook)


  def get_next_job(self):
    try:
      job = self.beanstalk.reserve()
      if job:
        job_body_str = job.body
        job.delete()
        job_dict = self.get_dict_from_json(job_body_str)
        print 'Worker %s, processing feed: %s' % (self.name, job_body_str)
        return job_dict
    except Exception as e:
      print 'Worker %s failed to get a job from queue ' % (self.name), traceback.format_exc()
      # Problem connecting to beanstalkd
      time.sleep(2)


  def process_job(self, feed):
    if feed:
      try:
        self.extract_feed(feed)
      except Exception as e:
        print 'Process job %s' % str(e)
        print 'Worker %s failed to process feed %s' % (self.name, str(feed)), traceback.format_exc()


  def extract_feed(self, feed):
    url = feed['url']
    try:
      feed_response = self.url_opener.open(url, timeout=self.feed_timeout)
      parsed_feed = feedparser.parse(feed_response.read())
    except Exception as e:
      print 'Worker %s failed to extract feed %s. Error: %s' % (self.name, url, repr(e))
      self.update_failure_count(feed)
      return

    items = self.get_feed_items(parsed_feed)
    hashed_url = self.hash_url(url)
    if items:
      try:
        print 'Saving feed....'
        self.save_feed(feed, items, hashed_url)
      except Exception as e:
         print 'Extract feed %s' % str(e)
    else:
      print 'No feed items found for url "%s"' % url
      self.update_failure_count(feed)

  # Memcache client in the Engine requires the key to be in this specific format
  def hash_url(self, url):
    url = url.decode('utf8')
    digest = hashlib.sha1(url).digest()
    b64digest = base64.encodestring(digest).strip().encode('string_escape')
    encdigest = list(urllib.quote_plus(b64digest, safe='()*!'))
    for i in xrange(len(encdigest)):
      if encdigest[i] == '%':
        encdigest[i + 1] = encdigest[i + 1].lower()
        encdigest[i + 2] = encdigest[i + 2].lower()
    return ''.join(encdigest)


  def update_failure_count(self, feed):
    try:
      self.feeds_to_refresh_collection.update({'_id': feed['_id']},
          {'$inc': {'failed_count': 1}, '$set': {'last_update_time': datetime.utcnow(), 'state': None}})
    except Exception as e:
      self.logger.error('Worker %s failed to update failure count for feed "%s"' % (self.name, feed['url']), traceback.format_exc())


  def get_feed_items(self, parsed_feed):
    items = []
    feed = self.get_feed_info(parsed_feed)
    top_items = self.get_top_items(parsed_feed['items'])

    for item in top_items:
      feed_item = {'feedTitle'    : feed['title'],
                    'source_feed' : feed['url'],
                    'logo_url'    : feed['logo'],
                    'feed_type'   : feed['type']}

      feed_item['title'] = item.get('title', '')
      feed_item['description'] = item.get('summary', '')
      if feed_item['description']:
        feed_item['description'] = feed_item['description'].split('<')[0]
        entities, html = self.get_yql_entities(feed_item['description'])
        feed_item['entities'] = entities
        feed_item['html'] = html
      feed_item['URL'] = item.get('link', '')
      feed_item['date_published'] = item.get('published', '')
      feed_item['image'] = self.get_image(item)
      items.append(feed_item)
    return items


  def get_yql_entities(self, text):
    try:
      res = self.yql.execute('select * from contentanalysis.analyze where text=%s;' % json.dumps(text))
      entities = res.rows[0]['entity']
    except:
      entities = []
    for row in entities:
      try:
        link = row['wiki_url']
        entity = row['text']['content']
        span_tag = '<span onclick="getInfobox(\'' + link + '\')" class="entity";>'
        text = text.replace(entity, span_tag + entity + '</span>')
      except:
        continue
    print text
    print '-------------------------\n'
    print entities
    print '-------------------------\n'
    return entities, text



  def get_top_items(self, items):
    try:
      sorted_items = sorted(items, key=lambda i: i['published_parsed'], reverse=True)
    except:
      sorted_items = items

    if len(sorted_items) > self.max_feed_items:
      sorted_items = sorted_items[:self.max_feed_items]
    return sorted_items


  def get_feed_info(self, parsed_feed):
    feed = {}
    try:
      feed['logo'] = parsed_feed['feed']['image']['href']
    except:
      feed['logo'] = ''

    try:
      feed['title'] = parsed_feed['feed']['title']
    except:
      feed['title'] = ''

    feed['type'] = parsed_feed.get('version', '').upper()

    try:
      feed['url'] = parsed_feed['feed']['title_detail']['base']
    except:
      feed['url'] = ''
    return feed


  def get_image(self, item):
    if 'media_content' in item:
      for content in item['media_content']:
        if 'url' in content:
          return content['url']
    return ''


  def save_feed(self, feed, items, hashed_url):
    if not items:
      print 'No items for feed: %s' % feed
      return
    try:
      self.mongo_handler.db.feeds_entities.save({'_id': hashed_url, 'items': items})
      print 'Saved items: %s' % items
      #import pprint
      #pp = pprint.PrettyPrinter(indent=4)
      #pp.pprint(items_str)

    except Exception as e:
      print e, traceback.format_exc()
      print 'Worker %s failed to save feed "%s" in memcache' % (self.name, feed['url'])

    #try:
      #self.feeds_to_refresh_collection.update({'url': feed['url']},
      #    {'$set': {'last_update_time': datetime.utcnow(), 'state': None}}, multi=True)
      #self.logger.debug('Worker %s, saved feed "%s" in key "%s"' % (self.name, feed['url'], hashed_url))
    #except Exception as e:
      #print e
      #self.logger.error('Worker %s failed to update last update time for feed "%s"' % (self.name, feed['url']), traceback.format_exc())


  def run(self):
    while True:
      job = self.get_next_job()
      if job:
        response = self.process_job(job)


  def exit(self):
    self.mongo_handler.close_connection()
    sys.exit(0)


if __name__ == '__main__':
  import sys

  if len(sys.argv) != 2:
    print 'USAGE: python %s <worker-name>' % (sys.argv[0])
    sys.exit(1)
  worker_name = sys.argv[1]

  worker = FeedsWorker(name=worker_name)
  worker.run()
  worker.exit()
