import os
import pymongo
from pymongo import Connection

from singleton import Singleton

CWD = os.path.dirname(__file__)

class MongoHandler():
  __metaclass__ = Singleton

  def __init__(self):

    try:
      self.db_connection = None
      self.init_config()
      self.init_db()
    except Exception as e:
      raise Exception('In MongoHandler init: ' + str(e))


  def init_config(self):
    self.db_connection_str = 'localhost:27017'
    #self.db_user = config_handler.get_key_from_config('db_user', 'admin')
    #self.db_password = config_handler.get_key_from_config('db_password', 'int311af33d')
    self.db_name = 'intellafeed'


  def init_db(self):
    self.db_connection = Connection(self.db_connection_str)
    self.db = self.db_connection[self.db_name]

    #self.db.authenticate(self.db_user, self.db_password)

  def close_connection(self):
    if self.db_connection:
      self.db_connection.close()
