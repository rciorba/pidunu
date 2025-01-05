from __future__ import print_function

from collections import defaultdict
from time import sleep
import os
import signal
import re

import docker
import pytest


CONTAINER_PYTHON_PATH = "/usr/local/bin/python"


class StreamHandler(object):
    def __init__(self, client, container):
        self.client = client
        self.container = container
        self.stream = container.attach(stdout=True, stderr=True, logs=True, stream=True)

    def wait(self, regexp=None):
        for line in self.stream:
            line = line.decode('utf8')
            if regexp is not None and regexp.match(line):
                break

    def split_logs_by_pid(self):
        """Parse the log lines and split by pid.
        Re-fetches the logs to avoid mixed lines in the stream.
        """
        logs = self.container.attach(
            stdout=True, stderr=True, logs=True, stream=False)
        logs_by_pid = defaultdict(list)
        for line in logs.splitlines():
            line = line.decode('utf8')
            pid, msg = line.split(":", 1)
            logs_by_pid[int(pid)].append(msg)
        return dict(logs_by_pid)


@pytest.fixture
def container_fixture(request):
    docker_url = os.getenv('DOCKER_URL', 'unix://var/run/docker.sock')
    docker_image = os.getenv('DOCKER_IMAGE', 'python:alpine')
    bind_mount = os.getenv('BIND_MOUNT_PATH', os.getcwd())
    func_name = request.function.__name__.replace("test_", "", 1)
    test_bin = f'/code/pidunu_dbg {CONTAINER_PYTHON_PATH} /code/test/bin/{func_name}.py'
    client = docker.DockerClient(base_url=docker_url, version='auto')
    container = client.containers.create(
        image=docker_image,
        detach=True,
        # volumes=['/code/'],
        volumes = {bind_mount: {'bind': '/code/', 'mode': 'ro'}},
        command=test_bin,
        name="snowflake",
    )
    request.addfinalizer(
        lambda: container.remove(force=True)
    )
    container.start()
    return client, container


def test_sigterm(container_fixture):
    """ Tests starting and stopping a container.

    Starts a container running a python program that prints
    to stdout any time it recieves a SIGTERM.

    Asserts that init passes SIGTERM to the child process,
    and that the child is reaped as expected.
    """
    client, container = container_fixture
    stream = StreamHandler(client, container)
    stream.wait(re.compile(r"\d+:term_py:start\n"))
    container.stop(timeout=1)
    stream.wait()
    logs = stream.split_logs_by_pid()
    p1_logs = logs[1]
    child_pid = int(p1_logs[1].rsplit(":", 1)[-1])
    expected = {}
    expected[1] = [
        "pidunu:main",
        "pidunu:child_pid: {}".format(child_pid),
        "pidunu:pid_one",
        # "pidunu:sig_handler:{}".format(signal.SIGTERM),
        "pidunu:child_died: {}".format(child_pid),
    ]
    expected[child_pid] = [
        "pidunu:fork=>0: {}".format(child_pid),
        f"pidunu:exec: {CONTAINER_PYTHON_PATH}",
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
    stream = StreamHandler(*container_fixture)
    stream.wait()
    logs = stream.split_logs_by_pid()
    p1_logs = logs[1]
    child_pid = int(p1_logs[1].rsplit(":", 1)[-1])
    expected = {}
    expected[1] = [
        "pidunu:main",
        "pidunu:child_pid: {}".format(child_pid),
        "pidunu:pid_one",
        "pidunu:reaped_orphan: {}".format(child_pid+2),
        "pidunu:child_died: {}".format(child_pid),
    ]
    expected[child_pid] = [
        "pidunu:fork=>0: {}".format(child_pid),
        f"pidunu:exec: {CONTAINER_PYTHON_PATH}",
    ]
    expected[child_pid+2] = [
        "child3 is done",
    ]
    assert logs == expected


def test_signals(container_fixture):
    """ Tests signal handling.
    """
    client, container = container_fixture
    stream = StreamHandler(client, container)
    stream.wait(re.compile(r"\d+:signals:start\n"))
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
        expected_line = "signals:{}:{}".format(name, signo)
        expected_child_output.append(expected_line)
        container.kill(signo)
        stream.wait(re.compile(".*"+expected_line))
    logs = stream.split_logs_by_pid()
    p1_logs = logs[1]
    child_pid = int(p1_logs[1].rsplit(":", 1)[-1])
    expected = [
        "pidunu:fork=>0: {}".format(child_pid),
        f"pidunu:exec: {CONTAINER_PYTHON_PATH}",
        "signals:start",
    ] + expected_child_output
    assert logs[child_pid] == expected


def test_return_code(container_fixture):
    """ Test return code is proxied correctly.
    """
    client, container = container_fixture
    assert container.wait().get("StatusCode") == 42
