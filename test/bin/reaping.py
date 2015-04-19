""" spawns 3 processes to test reaping
|-->  child1 - sleeps for 3 seconds
   |-->  child2 - prints message and dies
      |-->  child3 - sleeps for 1 second and dies
"""
from __future__ import print_function

from os import fork, getpid
from sys import exit  # pylint: disable=redefined-builtin
from time import sleep


def child3():
    sleep(.15)
    print("{}:child3 is done".format(getpid()))


def child2():
    pid = fork()
    if pid == 0:
        child3()
    elif pid > 1:
        pass
    else:
        exit(-1)


def child1():
    pid = fork()
    if pid == 0:
        child2()
    elif pid > 1:
        sleep(.3)
    else:
        exit(-1)


if __name__ == "__main__":
    child1()
