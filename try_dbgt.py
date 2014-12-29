#!/usr/bin/env python

import dbg
import threading
import time

def run(delay=0):
    thread_name = threading.current_thread().name
    time.sleep(delay)
    print "Look, here I am %s" % thread_name
    dbg.tsD()
    print "Let's try again %s" % thread_name
    dbg.tsD()
    print "We did it %s!" % thread_name

for n in range(3):
     threading.Thread(target=run, args=(1,)).start()

run()


