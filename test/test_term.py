from __future__ import print_function

from collections import defaultdict
from time import sleep

import docker
import pytest
import os


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
    client = docker.Client(base_url=docker_url)
    container = client.create_container(
        image=docker_image,
        volumes=['/code/'],
        command='/code/pidunu_dbg /usr/bin/python3 /code/test/bin/term.py',
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
        "pidunu:sig_handler; child_pid:{}".format(child_pid),
        "pidunu:child_died:{}".format(child_pid),
    ]
    expected[child_pid] = [
        "pidunu:fork=>0:{}".format(child_pid),
        "pidunu:exec:/usr/bin/python3",
        "term_py:start",
        "term_py:SIGTERM",
    ]
    assert logs == expected
