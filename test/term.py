""" prints message on sigterm
"""
from __future__ import print_function

import os
import sys
import signal
from time import sleep


def sigterm(_signal, _frame):
    sys.stdout.write("{}:term_py:SIGTERM\n".format(os.getpid()))
    sys.stdout.flush()
    sys.exit(0)


def child1():
    sys.stdout.write("{}:term_py:start\n".format(os.getpid()))
    sys.stdout.flush()
    signal.signal(signal.SIGTERM, sigterm)
    while True:
        sleep(1)


if __name__ == "__main__":
    child1()
