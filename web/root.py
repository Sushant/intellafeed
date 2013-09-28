import os
import sys
import json
import urllib
import cherrypy

CWD = os.path.dirname(__file__)

path = os.path.abspath(os.path.join(CWD, '..'))
if not path in sys.path:
    sys.path.insert(1, path)
del path

from lib import params
from lib import templates

class Root:
  @cherrypy.expose
  def index(self):
    template = templates.get('index.html')
    return template.render()

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

