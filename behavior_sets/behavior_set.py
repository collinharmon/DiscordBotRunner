from abc import ABC, abstractmethod

import threading
import queue

class BehaviorSet(ABC, threading.Thread):
  def __init__(self, *args, **kwargs):
    threading.Thread.__init__(self)
    if 'thread_ID' in kwargs is False or 'thread_name' in kwargs is False or 'event_queue' in kwargs is False or 'parent_queue' in kwargs is False:
      raise KeyError("Error: \"thread_ID\", \"thread_name\", \"event_queue\", and \"parent_queue\" must be provided to the BehaviorSet's ctor {k=v}")
    else:
      self.threadID = kwargs['thread_ID']
      self.name = kwargs['thread_name']
      self.event_queue = kwargs['event_queue']
      self.parent_queue = kwargs['parent_queue']
      """
      if isinstance(self.event_queue, queue) is False:
        raise ValueError("Parent must pass valid message queue to BehaviorSet thread")
      elif isinstance(self.parent_queue, queue) is False:
        raise ValueError("Parent must pass valid message queue to BehaviorSet thread")
      """

  def run(self):
    self.handle_discord_event_loop()

  @abstractmethod
  def handle_discord_event_loop(self):
    pass

  def get_queue(self):
    return self.event_queue