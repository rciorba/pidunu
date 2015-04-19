## Pidunu - a trivial init process, for use in Docker containers.

### What does pidunu do?
Pidunu does one thing and one thing only: it will start one process, and reap
any children untill the spawned child exits, at wich point it will exit as well.
Since "docker stop" sends a sigterm to the process it spawned in the container,
Pidunu is wellbehaved and passes along SIGTERM to the spawned child.

### Can it manage multiple processes?
No. Run an actual init daemon or look at something like supervisord to use
together with pidunu.

### Why is this useful?
Basically to avoid zombie processes in your containers.
Any process that exits, still gets tracked by the kernel until it's parrent
calls wait, this ensures the parent can find out about the return code of exited
subprocesses. Untill that happens the process is said to be in a Zombie state.
If your process spawns a child process, and that process spawns it's own children
and exits before they terminate, those children are inherited by PID1.
On traditional *nixe PID1 has the special responsibillity of calling wait on any
child. When using Docker, traditionally your process will be the first one spawned,
thus becoming PID1 for your container.
I sugest you read this great explanation:
http://blog.phusion.nl/2015/01/20/docker-and-the-pid-1-zombie-reaping-problem/

### Is this a stable/mature project?
This is definitely not a mature project, however there are tests and I use it
in a couple of places and it seems to do the job quite well.
The whole thing is just under 90 lines of vanilla C code which you can review
for yourself.

### Building from source

    make

### Running the tests
The tests are written using the pytest framework and the docker python bindings.
It's recommended you setup a virtualenv to install the python dependencies to
ensure you don't mess up your system's python packages.

If you don't have virtualenv installed follow the instructions here:
https://virtualenv.pypa.io/en/latest/installation.html

    virtualenv ve_pidunu
    source ve_pidunu/bin/activate
    pip install -r test/dependencies.txt

Now that we have installed the python dependencies we can run the tests like so:

    make test  # this also compiles the debug target for us
