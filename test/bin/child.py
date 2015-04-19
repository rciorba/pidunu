""" spawns 3 processes to test reaping
|-->  child1 - sleeps for 2 seconds
   |-->  child2 - prints message and dies
      |-->  child3 - sleeps for 1 second and dies
"""
from __future__ import print_function

import os
import sys
from time import sleep


def child3():
    sleep(1)
    print("child3 is done")


def child2():
    sleep(1)
    pid = os.fork()
    if pid == 0:
        child3()
    elif pid > 1:
        print("child2 is done")
    else:
        sys.exit(-1)


def child1():
    pid = os.fork()
    if pid == 0:
        child2()
    elif pid > 1:
        print("bye")
        sleep(3)
    else:
        sys.exit(-1)


if __name__ == "__main__":
    child1()
