#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <errno.h>


int pid_one(int child_pid) {
  int status;
  pid_t pid;
  while(1) {
    pid = wait(&status);
    if (pid == child_pid){
      // the spawned child just terminated
      return 0;
    }
  }
}

void execute(int argc, char** argv) {
  if (argc == 0)
    return;
  char* cmd = argv[0];
  char** rest = argv+1;
  if (execv(cmd, rest) == -1) {
    fprintf(stderr, "failed to exec %s, errno is %d\n", cmd, errno);
  }
}

int main(int argc, char** argv) {
  pid_t pid = fork();
  if (pid<0) {
    fprintf(stderr, "failed to fork, errno: %d\n", errno);
    return -1;
  } else if (pid > 0) {
    return pid_one(pid);
  } else if (pid == 0) {
    execute(argc, argv);
    return -128; // program should have called exec and we should never get here
  }
  return -127; // if we reach this we messed up somehow
}
