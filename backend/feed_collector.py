import os
import sys
import time
import json
import urllib2
import traceback


from datetime import datetime, timedelta

CWD = os.path.dirname(__file__)

path = os.path.abspath(os.path.join(CWD, '..'))
if not path in sys.path:
    sys.path.insert(1, path)
del path

from lib.mongo_handler import MongoHandler
#from utils.logger import MultiProcessLogger
#from utils.mongo_handler import MongoHandler
#from utils.config_handler import ConfigHandler

DEFAULT_TIMESTAMP = datetime.strptime('2011-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')

class FeedsCollector:
  def __init__(self):
    self.logger = None
    try:
      self.init_db()
      #self.init_logger()
      #self.logger.info('Feeds collector started in %s mode' % env)
    except Exception as e:
      #if self.logger:
      #  self.logger.error('In FeedsCollector init ', traceback.format_exc())
      raise Exception(e)


  def init_db(self):
    self.mongo_handler = MongoHandler()
    self.feeds_to_refresh_collection = self.mongo_handler.db['feeds_to_refresh1']
    #self.feeds_to_refresh_collection.ensure_index('url')


  #def init_logger(self):
  #  self.logger = MultiProcessLogger(self.logger_url)


  def get_all_profiles(self):
    try:
      profiles = list(self.profiles_collection.find())
      return profiles
    except Exception as e:
      print 'Failed to get feeds: %s', traceback.format_exc()


  def get_feeds_from_profiles(self):
    all_feeds = set()
    for user_feeds in list(self.mongo_handler.db.user_feeds2.find()):
      try:
        feeds = user_feeds['feeds']

        for feed in feeds:
          all_feeds.add(feed)
      except Exception as e:
        print 'Failed to extract feeds from profile %d\n%s' % p['_id'], traceback.format_exc()
        continue

    return list(all_feeds)


  def get_all_category_feeds(self):
    feeds_set = set()
    try:
      category_feeds = list(self.feeds_collection.find({}, {'url': 1}))
      for feed in category_feeds:
        feeds_set.add(feed['url'])
    except Exception as e:
      pass
      #self.logger.error('Failed to get category feeds: %s' % str(e), traceback.format_exc())
    return list(feeds_set)


  def add_new_feeds(self, feeds):
    new_feeds = []
    for feed in feeds:
      try:
        feed_doc = self.mongo_handler.db.feeds_to_refresh1.find_one({'url': feed})
        if not feed_doc:
          new_feeds.append({'url': feed, 'failed_count': 0, 'last_update_time': DEFAULT_TIMESTAMP})
      except Exception as e:
        #self.logger.error('Failed to get feed %s from db' % feed, traceback.format_exc())
        continue
    self.add_new_feeds_to_db(new_feeds)


  def add_new_feeds_to_db(self, new_feeds):
    print new_feeds
    if new_feeds:
      try:
        self.feeds_to_refresh_collection.insert(new_feeds, continue_on_error=True)
        #self.logger.debug('Added following new feeds to db: %s' % repr(new_feeds))
      except Exception as e:
        pass
        #self.logger.error('Failed to add new feeds to db', traceback.format_exc())


  def run(self):
    all_feeds = self.get_feeds_from_profiles()
    self.add_new_feeds(all_feeds)
    #self.exit()


  def exit(self):
    self.mongo_handler.close_connection()
    sys.exit(0)


if __name__ == '__main__':
  fc = FeedsCollector()
  while True:
    fc.run()
    time.sleep(5)
