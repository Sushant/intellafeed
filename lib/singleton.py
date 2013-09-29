"""
Metaclass for creating singletons. Extends type function to 
only return an existing instances of a class. Replaces type as your metaclass.
To use, put __metaclass__ = Singleton in the class you want to behave as a Singleton

eg: 
class MongoHandler():
   __metaclass__ = Singleton
"""

class Singleton(type):
  _instances = {}
  def __call__(cls, *args, **kwargs):
    if cls not in cls._instances:
      cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
    return cls._instances[cls]
