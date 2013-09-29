'''
@module: queue_handler.py
@description: Base module for all producer/consumer modules for reading IP/port of the Queue server,
setting up queue connections, and a provision to 'use' or 'watch' the queue for Producer and Consumer, respectively.
'''

import os
import beanstalkc
import sys
import traceback

import os
import socket
socket.setdefaulttimeout(None)

CWD = os.path.dirname(__file__)

'''
Base module for all producer/consumer modules for reading IP/port of the Queue server,
setting up queue connections, and a provision to 'use' or 'watch' the queue for Producer and Consumer, respectively.
'''
class QueueHandler():

  '''
  Constructor for QueueHandler.
  @params: 'is_producer' => If True, 'use' the queue, else 'watch' the queue.
  '''
  def __init__(self, is_producer=False, queue_name='default'):
    self.beanstalk = None

    try:
      job_queue_ip = '127.0.0.1'
      job_queue_port = 11300

      # Establish a beanstalk connection
      self.beanstalk = beanstalkc.Connection(host = job_queue_ip, port = int(job_queue_port))
      if self.beanstalk:
        if is_producer:
          # Producer should 'use' the queue
          self.beanstalk.use(queue_name)
        else:
          # Consumer should 'watch' the queue.
          self.beanstalk.watch(queue_name)
    except Exception as init_ex:
      raise Exception('QueueHandler.__init()__: %s, %s' % (init_ex, traceback.format_exc()))


  def close_connection(self):
    try:
      if self.beanstalk:
        self.beanstalk.close()
    except Exception as close_connection_ex:
      raise Exception('QueueHandler.close_connection(): %s, %s' % (close_connection_ex, traceback.format_exc()))
