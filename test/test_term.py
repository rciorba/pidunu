from __future__ import print_function

from collections import defaultdict
from time import sleep
import os
import signal
import re

import docker
import pytest


def split_logs_by_pid(logs):
    logs_by_pid = defaultdict(list)
    for line in logs.splitlines():
        pid, msg = line.split(":", 1)
        logs_by_pid[int(pid)].append(msg)
    return dict(logs_by_pid)


@pytest.fixture
def container_fixture(request):
    docker_url = os.getenv('DOCKER_URL', 'unix://var/run/docker.sock')
    docker_image = os.getenv('DOCKER_IMAGE', 'ubuntu:latest')
    bind_mount = os.getenv('BIND_MOUNT_PATH', os.getcwd())
    test_bin = '/code/pidunu_dbg /usr/bin/python3 /code/test/bin/{}.py'.format(
        request.function.__name__.replace("test_", "", 1)
    )
    client = docker.Client(base_url=docker_url)
    container = client.create_container(
        image=docker_image,
        volumes=['/code/'],
        command=test_bin,
        name="snowflake",
    )
    request.addfinalizer(
        lambda: client.remove_container(container.get("Id"), force=True))
    binds = {bind_mount: {'bind': '/code/', 'ro': True}}
    client.start(container.get("Id"), binds=binds)
    return client, container


def test_sigterm(container_fixture):
    """ Tests starting and stopping a container.

    Starts a container running a python program that prints
    to stdout any time it recieves a SIGTERM.

    Asserts that init passes SIGTERM to the child process,
    and that the child is reaped as expected.
    """
    client, container = container_fixture
    sleep(.2)
    client.stop(container.get("Id"), timeout=1)
    logs = split_logs_by_pid(
        client.attach(container, stdout=True, stderr=True, logs=True))
    p1_logs = logs[1]
    child_pid = int(p1_logs[1].rsplit(":", 1)[-1])
    expected = {}
    expected[1] = [
        "pidunu:main",
        "pidunu:child_pid:{}".format(child_pid),
        "pidunu:pid_one",
        "pidunu:sig_handler:{}".format(signal.SIGTERM),
        "pidunu:child_died:{}".format(child_pid),
    ]
    expected[child_pid] = [
        "pidunu:fork=>0:{}".format(child_pid),
        "pidunu:exec:/usr/bin/python3",
        "term_py:start",
        "term_py:SIGTERM",
    ]
    assert logs == expected


def test_reaping(container_fixture):
    """ Tests reaping of other inherited children.

    Starts a container running a python program that spawns a
    process tree 3 layers deep.
    |-->  child1 - sleeps for 2 seconds
       |-->  child2 - prints message and dies
          |-->  child3 - sleeps for 1 second and dies

    Asserts that init reaps orphaned process child3.
    """
    client, container = container_fixture
    sleep(.5)
    logs = split_logs_by_pid(
        client.attach(container, stdout=True, stderr=True, logs=True))
    p1_logs = logs[1]
    child_pid = int(p1_logs[1].rsplit(":", 1)[-1])
    expected = {}
    expected[1] = [
        "pidunu:main",
        "pidunu:child_pid:{}".format(child_pid),
        "pidunu:pid_one",
        "pidunu:reaped_orphan:{}".format(child_pid+2),
        "pidunu:child_died:{}".format(child_pid),
    ]
    expected[child_pid] = [
        "pidunu:fork=>0:{}".format(child_pid),
        "pidunu:exec:/usr/bin/python3",
    ]
    expected[child_pid+2] = [
        "child3 is done",
    ]
    assert logs == expected


def test_signals(container_fixture):
    """ Tests signal handling.
    """
    client, container = container_fixture
    sleep(.2)
    signame_re = re.compile("^SIG[A-Z0-9]+$")
    expected_child_output = []
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
        expected_child_output.append(
            "signals:{}:{}".format(name, signo))
        client.kill(container.get("Id"), signo)
        sleep(0.01)
    logs = split_logs_by_pid(
        client.attach(container, stdout=True, stderr=True, logs=True))
    p1_logs = logs[1]
    child_pid = int(p1_logs[1].rsplit(":", 1)[-1])
    expected = [
        "pidunu:fork=>0:{}".format(child_pid),
        "pidunu:exec:/usr/bin/python3",
        "signals:start",
    ] + expected_child_output
    assert logs[child_pid] == expected
