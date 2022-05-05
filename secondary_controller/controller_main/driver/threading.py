import _thread, gc

import driver.utils as utils


class ThreadSafeQueue:
  """ A queue that can be used across different threads """

  def __init__(self, size: int = 30) -> None:
    """ Initialize the queue, allocation buffer
        `size`: size of the buffer """
    self.__start = 0
    self.__end = 0
    self.__size = size
    self.__queue = [None] * self.__size
    self.__lock = _thread.allocate_lock()
    self.__empty = True

  def enqueue(self, item, blocking: bool=True) -> bool:
    """ Enqueue the given item to the end of the buffer
        `item`: item to be appended to the buffer
        `blocking`: if the operation is blocking 
        `returns`: whether the operation is a success"""
    self.__lock.acquire(blocking)
    if not self.__empty and self.__end == self.__start:
      self.__lock.release()
      return False
    self.__queue[self.__end] = item
    self.__end = (self.__end + 1) % self.__size
    self.__empty = False
    self.__lock.release()
    return True

  def dequeue(self, blocking: bool=True):
    """ Dequeue and return from the head of the buffer
        `blocking`: if the operation is blocking 
        `returns`: an item at the head of the queue, None if a failure"""
    self.__lock.acquire(blocking)
    if self.__empty:
      self.__lock.release()
      return None
    item = self.__queue[self.__start]
    self.__start = (self.__start + 1) % self.__size
    self.__empty = self.__start == self.__end
    self.__lock.release()
    return item

  def is_empty(self) -> bool:
    """ Check if the queue is now empty
        `returns`: whether the queue is empty """
    self.__lock.acquire()
    ret = self.__empty
    self.__lock.release()
    return ret

  def clear(self) -> None:
    """ Clear the queue without erasing contents, only head / tail pointers are reset """
    self.__lock.acquire()
    self.__start = 0
    self.__end = 0
    self.__empty = True
    self.__lock.release()

  def print_queue(self) -> None:
    """ Print the current status of the queue, for debug use """
    self.__lock.acquire()
    print(f"Start: {self.__start}, End: {self.__end}, Size: {self.__size}, Empty: {self.__empty}")
    print(self.__queue)
    self.__lock.release()


class Thread:
  """ Custom thread class, manage basic level multi-threading operations 
      Notice, for unknown reason, ESP32 seems only supporting 3 concurrent threads at the same time """
  thread_pool = {}
  thread_pool_lock = _thread.allocate_lock()

  def __init__(self, func) -> None:
    """ Create a Thread object using the desired function to be run in a new thread """
    self.__func = func

  def run(self, *args: tuple, **kwargs: dict) -> None:
    """ Run the give thread using possible arguments """
    _thread.start_new_thread(self.__thread_wrapper, args, kwargs)

  def __thread_wrapper(self, *args: tuple, **kwargs: dict) -> None:
    """ Wrapper function that used to retrieve properties corresponding to the thread.
        Should NOT be called """
    Thread.thread_pool_lock.acquire()
    # get identifier of thread and add itself to thread pool using that identifier
    identifier = _thread.get_ident()
    Thread.thread_pool[identifier] = [self.__func.__name__, self]
    Thread.thread_pool_lock.release()

    self.__func(*args, **kwargs)
    
    # remove itself from thread pool
    Thread.thread_pool_lock.acquire()
    utils.ASSERT_TRUE(identifier in Thread.thread_pool, "Thread identity does not exist")
    Thread.thread_pool.pop(identifier)
    Thread.thread_pool_lock.release()
    # manually call garbage collector and exit thread
    gc.collect()
    _thread.exit()

  @classmethod
  def report_all_threads(cls) -> None:
    """ Report all threads that are currently running, for debug use """
    Thread.thread_pool_lock.acquire()
    print(cls.thread_pool)
    Thread.thread_pool_lock.release()
