""" Tests handling of sigterm.
"""
from __future__ import print_function

from collections import defaultdict
from time import sleep

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
    client = docker.Client(base_url='unix://var/run/docker.sock')
    container = client.create_container(
        image='ubuntu:latest',
        volumes=['/code/'],
        command='/code/pidunu_dbg /usr/bin/python3 /code/test/term.py',
        name="snowflake",
    )
    binds = {'/home/rciorba/repos/pidunu/': {'bind': '/code/', 'ro': True}}
    client.start(container.get("Id"), binds=binds)
    request.addfinalizer(
        lambda: client.remove_container(container.get("Id"), force=True))
    return client, container


def test_sigterm(container_fixture):
    client, container = container_fixture
    sleep(.1)
    client.stop(container.get("Id"), timeout=0)
    logs = split_logs_by_pid(
        client.attach(container, stdout=True, logs=True))
    p1_logs = logs[1]
    child_pid = int(p1_logs[1].rsplit(":", 1)[-1])
    expected = {}
    expected[1] = [
        "pidunu:main",
        "pidunu:child_pid:{}".format(child_pid),
        "pidunu:pid_one",
        "pidunu:sig_handler; child_pid:{}".format(child_pid),
    ]
    expected[child_pid] = [
        "pidunu:fork=>0:{}".format(child_pid),
        "pidunu:exec:/usr/bin/python3",
        "term_py:start",
        "term_py:SIGTERM",
    ]
    assert logs == expected
