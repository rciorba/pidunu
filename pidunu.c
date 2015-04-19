#define _POSIX_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <signal.h>
#include <errno.h>

#ifdef _DEBUG
#define DEBUG 1
#else
#define DEBUG 0
#endif

#define debug_print(fmt, ...)                   \
  do {                                          \
    if (DEBUG) {                                \
      fprintf(stderr, "%d:pidunu:", getpid());  \
      fprintf(stderr, fmt, __VA_ARGS__);        \
      fflush(NULL);                             \
    }                                           \
  } while (0)

pid_t g_child_pid = 0;

void sig_handler(int signo) {
  debug_print("sig_handler; child_pid:%d\n", g_child_pid);
  if (g_child_pid > 1) {
    kill(g_child_pid, signo);
  }
  signal(signo, sig_handler); // re-registr the signal
}

void setup_signals(pid_t child_pid) {
  g_child_pid = child_pid;
  if (signal(SIGTERM, sig_handler) == SIG_ERR) {
    debug_print("failed to setup SIGTERM; errno:%d", errno);
    exit(-2);
  };
}

int pid_one(pid_t child_pid) {
  int status;
  pid_t pid;
  debug_print("%s\n", "pid_one");
  setup_signals(child_pid);
  while(1) {
    pid = wait(&status);
    if (pid == child_pid) {
      // the spawned child just terminated
      debug_print("child_died:%d\n", pid);
      return 0;
    }
    if(DEBUG)  // will get optimized away by the compiler
      if(pid!=-1)  // ignore we might have no children in a suitable state
        debug_print("reaped_orphan:%d\n", pid);
  }
}

void execute(int argc, char** argv) {
  if (argc <= 1)
    return;
  char* cmd = argv[1];
  char** args = argv+1;
  debug_print("exec:%s\n", cmd);
  if (execv(cmd, args) == -1) {
    fprintf(stderr, "failed to exec %s, errno is %d\n", cmd, errno);
  }
}

int main(int argc, char** argv) {
  debug_print("%s", "main\n");
  pid_t pid = fork();
  if (pid<0) {
    fprintf(stderr, "failed to fork, errno: %d\n", errno);
    return -1;
  } else if (pid > 0) {
    debug_print("child_pid:%d\n", pid);
    return pid_one(pid);
  } else if (pid == 0) {
    debug_print("fork=>0:%d\n", getpid());
    execute(argc, argv);
    return -128; // program should have called exec and we should never get here
  }
  return -127; // if we reach this we messed up somehow
}
