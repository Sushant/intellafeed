"""
  Looks at all feeds that need to be updated and puts them in a queue
"""
import os
import sys
import time
import json
from datetime import datetime, timedelta
from bson import json_util

CWD = os.path.dirname(__file__)

path = os.path.abspath(os.path.join(CWD, '..'))
if not path in sys.path:
    sys.path.insert(1, path)
del path

#from utils.logger import RallyverseLogger
#from utils.queue_handler import QueueHandler
#from utils.mongo_handler import MongoHandler

from lib.mongo_handler import MongoHandler
from lib.queue_handler import QueueHandler

CWD = os.path.dirname(__file__)
#CONFIG_PATH = os.path.abspath(os.path.join(CWD, '../config/feeds.yaml'))
#LOG_DIR = os.path.abspath(os.path.join(CWD, '../logs/feeds_producer'))
#LOG_FILENAME = 'feeds_producer.log'
#LOGGER_NAME = 'FeedsProducer'


class FeedsProducer(QueueHandler):
  def __init__(self):
    #self.logger = None
    try:
      #self.init_logger()
      QueueHandler.__init__(self, is_producer=True, queue_name='feeds_queue')
      self.init_config()
      self.init_db()
      #self.logger.info('Feeds producer started in %s mode' % env)
    except Exception as e:
      #if self.logger:
      #  self.logger.exception('In FeedsProducer init: ')
      raise Exception(e)


  #def init_logger(self):
  #  self.logger = RallyverseLogger(LOG_DIR, LOG_FILENAME, LOGGER_NAME).get_logger()


  def init_config(self):
    self.sleep_time_in_sec = 5
    self.feed_freshness = 60
    self.bulk_processing_size = 50


  def init_db(self):
    self.mongo_handler = MongoHandler()
    self.feeds_to_refresh_collection = self.mongo_handler.db['feeds_to_refresh1']


  def queue_feeds(self):
    try:
      refresh_window = datetime.utcnow() - timedelta(minutes=self.feed_freshness)
      feeds = list(self.feeds_to_refresh_collection.find({'last_update_time': {'$lte': refresh_window}},
        {'url': 1}).limit(self.bulk_processing_size))
      #feeds = list(self.feeds_to_refresh_collection.find({},{'url': 1}).limit(self.bulk_processing_size))
      print feeds
    except Exception as e:
      print e
      pass
      #self.logger.exception('Unable to get feeds from database: ')
      return

    for feed in feeds:
      self.add_feed_to_queue(feed)


  def add_feed_to_queue(self, feed):
    feed_str = self.get_json_str(feed)
    try:
      self.beanstalk.put(feed_str)
      print feed
      #self.logger.debug('Added feed %s to queue' % feed['url'])
    except Exception as e:
      pass
      #self.logger.exception('Failed to queue feed %s for processing:' % str(feed['url']))
      return

    try:
      self.feeds_to_refresh_collection.update({'_id': feed['_id']},
          {'$set': {'state': 'queued', 'last_update_time': datetime.utcnow()}})
    except Exception as e:
      print e
    #  pass
      #self.logger.error('Failed to update state for feed "%s"' % (self.name, feed['url']), traceback.format_exc())


  def get_json_str(self, feed):
    return json.dumps(feed, default=json_util.default)


  def run(self):
    self.queue_feeds()

  def exit(self):
    self.mongo_handler.close_connection()
    sys.exit(0)


if __name__ == '__main__':
  fp = FeedsProducer()
  while True:
    fp.run()
    time.sleep(fp.sleep_time_in_sec)
  fp.exit()
