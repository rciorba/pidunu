#define _POSIX_SOURCE
#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <signal.h>
#include <errno.h>

#define DEBUG 1

#define debug_print(fmt, ...) \
  do { if (DEBUG) printf(fmt, __VA_ARGS__); fflush(NULL);} while (0)

pid_t g_child_pid = 0;

static void sigint(int signo) {
  if (g_child_pid > 1) {
    kill(g_child_pid, SIGINT);
  }
  signal(SIGINT, sigint); // re-registr the signal
}

void setup_signals(pid_t child_pid){
  g_child_pid = child_pid;
  signal(SIGINT, sigint);
}

int pid_one(pid_t child_pid) {
  int status;
  pid_t pid;
  setup_signals(child_pid);
  debug_print("%d\t pid_one\n", getpid());
  while(1) {
    pid = wait(&status);
    if (pid == child_pid){
      // the spawned child just terminated
      debug_print("child died: %d\n", pid);
      return 0;
    }
    /* debug_print("died: %d\n", pid); */
  }
}

void execute(int argc, char** argv) {
  if (argc <= 1)
    return;
  char* cmd = argv[1];
  char** args = argv+1;
  debug_print("%d\t %s ", getpid(), cmd);
  if (execv(cmd, args) == -1) {
    fprintf(stderr, "failed to exec %s, errno is %d\n", cmd, errno);
  }
}

int main(int argc, char** argv) {
  debug_print("%d\t main\n", getpid());
  pid_t pid = fork();
  if (pid<0) {
    fprintf(stderr, "failed to fork, errno: %d\n", errno);
    return -1;
  } else if (pid > 0) {
    debug_print("%d\t pid unu\n", getpid());
    return pid_one(pid);
  } else if (pid == 0) {
    debug_print("%d\t pid 0\n", getpid());
    execute(argc, argv);
    return -128; // program should have called exec and we should never get here
  }
  return -127; // if we reach this we messed up somehow
}
