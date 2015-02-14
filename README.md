## Pidunu - a trivial init process, for use in Docker containers.

### What does pidunu do?
Pidunu will start one process, and reap any child untill the spawned child
exits, at wich point it will exit as well.

### Why is this useful?
I sugest you read this great explanation:
http://blog.phusion.nl/2015/01/20/docker-and-the-pid-1-zombie-reaping-problem/

### Is this a stable/mature project?
It still doesn't handle signals, and there are some open questions about
what should be done with stdout/stderr and the return code of the spawned
child.
