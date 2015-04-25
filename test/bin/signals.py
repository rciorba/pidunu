from __future__ import print_function

import os
import re
import signal
import sys
from time import sleep


def sighandler(name, signo):
    def handler(signo, _frame):
        sys.stdout.write("{}:signals:{}:{}\n".format(os.getpid(), name, signo))
        sys.stdout.flush()
    signal.signal(signo, handler)


def child1():
    sys.stdout.write("{}:signals:start\n".format(os.getpid()))
    sys.stdout.flush()
    signame_re = re.compile("^SIG[A-Z0-9]+$")
    blacklist = (
        "SIGSTOP", "SIGKILL",  # can't be registered
        "SIGRTMIN", "SIGRTMAX",  # max and min for posix realtime signals
        "SIGIOT",  # duplicate of SIGABRT
        "SIGPOLL",  # duplicate of SIGIO
        "SIGCHLD", "SIGCLD",  # pidunu will not pass these on
    )
    signals = [(name, getattr(signal, name)) for name in dir(signal)
               if signame_re.match(name) and name not in blacklist]
    signals += [("SIGSTKFLT", 16), ]
    for name, signo in signals:
        sighandler(name, signo)
    while True:
        sleep(1)


if __name__ == "__main__":
    child1()
