from threading import Thread
from time import sleep
from logging import getLogger
from json import load,\
    dump
from traceback import format_exc

class json_ops_daemon_thread():

    def __init__(self):
        self._log = getLogger()

    def loop(self):
        def slave():
            while True:
                self._log.info('thread looping')
                sleep(1)
        Thread(target=slave).start()

class json_ops_class():

    def __init__(self):
        self._log = getLogger()

    def return_input(self,
                     input):
        return input
