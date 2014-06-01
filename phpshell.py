#!/usr/bin/python
import subprocess
import threading
import sys
import os
from multiprocessing import Pipe

class PhpProcessor():
  COMMAND = 'php -a'
  MAGIC = os.urandom(8).encode('hex')

  def __init__(self):
    self.process = subprocess.Popen(COMMAND.split(' '), stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    self.pipe, consumer_pipe = Pipe()
    self.condition = None

    def consume():
      process.stdout.read(26)
      magic_state = 0
      buf = ""
      while True:
        output = process.stdout.read(1)
        if not output and process.poll():
          break
        if output:
          if output == MAGIC[magic_state[0]]:
            magic_state += 1
            if magic_state == len(MAGIC):
              magic_state = 0
              consumer_pipe.send(buf)
              if self.condition:
                self.condition.notify_all()
          else:
            if magic_state > 0:
              buf += MAGIC[:magic_state]
              magic_state = 0
            buf += output
    consumer = threading.Thread(target=consume, name='phpshell_consumer')
    consumer.start()

  def close(self):
    self.process.terminate()
    self.process.wait()

  def execute(self, cmd):
    #TODO do stuff with command
    if self.condition:
      self.condition.acquire()
    self.condition = threading.Condition()
    self.process.stdin.write(cmd+'\n'+'echo "%s"' % MAGIC)
    #return self.condition
    self.condition.acquire()
    return self.pipe.recv()
