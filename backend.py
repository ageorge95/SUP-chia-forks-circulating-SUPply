from threading import Thread
from time import sleep

class json_ops_daemon_thread():
    def __init__(self):
        pass

    def loop(self):
        def slave():
            while True:
                print('thread looping')
                sleep(1)
        Thread(target=slave).start()

class json_ops_class():

    def return_input(self,
                     input):
        return input
