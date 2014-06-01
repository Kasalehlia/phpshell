#!/usr/bin/env python2
import subprocess
import threading
import readline
import atexit
import sys
import os
from multiprocessing import Pipe

class PhpProcessor():
  COMMAND = 'php -a'
  MAGIC = os.urandom(8).encode('hex')

  def __init__(self):
    self.process = subprocess.Popen(self.COMMAND.split(' '), stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    self.pipe, consumer_pipe = Pipe()
    self.condition = threading.Event()
    self.condition.set()

    def consume():
      # read php interpreter stuff
      while self.process.stdout.read(1) != "\n":
        pass
      self.process.stdout.read(1)
      magic_state = 0
      buf = ""
      while True:
        output = self.process.stdout.read(1)
        if not output and self.process.poll():
          break
        if output:
          if output == self.MAGIC[magic_state]:
            magic_state += 1
            if magic_state == len(self.MAGIC):
              magic_state = 0
              consumer_pipe.send(buf)
              if self.condition:
                self.condition.set()
                pass
          else:
            if magic_state > 0:
              buf += self.MAGIC[:magic_state]
              magic_state = 0
            buf += output
      self.condition.set()
    consumer = threading.Thread(target=consume, name='phpshell_consumer')
    consumer.start()

  def close(self):
    self.process.terminate()
    self.process.wait()

  def execute(self, cmd):
    #TODO do stuff with command
    self.condition.wait()
    self.condition.clear()
    self.process.stdin.write('var_dump(%s);echo "%s";\n' % (cmd,self.MAGIC))
    self.process.stdin.flush()
    self.condition.wait()
    return self.pipe.recv()

class PhpConsole:
  def __init__(self, histfile=".phpshell"):
    self.init_history(os.path.expanduser(histfile))
    self.php = PhpProcessor()

  def init_history(self, histfile):
    if hasattr(readline, "read_history_file"):
      try:
        readline.read_history_file(histfile)
      except IOError:
        pass
      atexit.register(self.save_history, histfile)

  def save_history(self, histfile):
    readline.write_history_file(histfile)

  def run(self):
    while True:
      try:
        input = raw_input(">")
      except (KeyboardInterrupt, EOFError):
        break
      self.handle_input(input)
  def handle_input(self, input):
    print self.php.execute(input)

if __name__ == "__main__":
  print "do not use php!"
  phpshell = PhpConsole("~/.phpshell")
  phpshell.run()
