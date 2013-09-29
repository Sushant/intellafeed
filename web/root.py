import os
import sys
import json
import base64
import urllib
import hashlib
import cherrypy

CWD = os.path.dirname(__file__)

path = os.path.abspath(os.path.join(CWD, '..'))
if not path in sys.path:
    sys.path.insert(1, path)
del path

from lib import params
from lib import templates
from lib import mongo_handler

class Root:

  def __init__(self):
    self.mongo = mongo_handler.MongoHandler()


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

  @cherrypy.expose
  def index(self):
    template = templates.get('index.html')
    user_items = []
    user_feeds = self.mongo.db.user_feeds1.find_one({'_id': 1})['feeds']
    for feed in user_feeds:
      url = self.hash_url(feed)
      feed_items = self.mongo.db.feeds_entities.find_one({'_id': url})
      if feed_items:
        feed_items = feed_items['items']
        for item in feed_items:
          user_items.append(item)
    return template.render({'feed_items': user_items})

  @cherrypy.expose
  def settings(self):
    template = templates.get('settings.html')
    return template.render()

  @cherrypy.expose
  def save_settings(self, *args, **kwargs):
    print kwargs
    feeds = []
    for k, v in kwargs.iteritems():
      if k.startswith('item'):
        feeds.append(v)
    try:
      self.mongo.db.user_feeds1.save({'_id': 1, 'feeds': feeds})
    except Exception as e:
      print e
    pass


if __name__ == '__main__':

  config = {
    'global': {
      'server.socket_host': "0.0.0.0",
            'server.socket_port': params.WEB_PORT,
            'server.thread_pool': 10,
            'engine.autoreload_on':False,
        },
        '/': {
            'tools.staticdir.root': params.WEB_DIR,
            'tools.sessions.on': True,
            'tools.sessions.timeout': 300,
            'tools.gzip.on': True,
        },
        '/images': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': "images",
        },
        '/css': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': "css",
        },
        '/js': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': "js",
        }
  }

  cherrypy.config.update(config['global'])
  app = cherrypy.tree.mount(Root(), config=config)


  try:
    cherrypy.engine.start()
    print 'Successfully started the Quest Panel'
    cherrypy.engine.block()
  except socket.error, fault:
    print 'Unable to start Quest Panel: ', fault

