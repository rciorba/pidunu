#define _POSIX_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <signal.h>
#include <errno.h>
#include <sysexits.h>

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
  /* debug_print("sig_handler:%d\n", signo); */
  if (g_child_pid > 1) {
    kill(g_child_pid, signo);
  }
  signal(signo, sig_handler); // re-registr the signal
}

void register_signal(int signo, const char* signame){
  if (signal(signo, sig_handler) == SIG_ERR) {
    debug_print("failed to setup %s; errno: %d", signame, errno);
    exit(-2);
  };
}

void setup_signals(pid_t child_pid) {
  g_child_pid = child_pid;
  register_signal(SIGABRT, "SIGABRT");
  register_signal(SIGALRM, "SIGALRM");
  register_signal(SIGBUS, "SIGBUS");
  /* if we have an inherited child die, don't send SIGCHLD to the spawned child
  register_signal(SIGCHLD, "SIGCHLD");
  register_signal(SIGCLD, "SIGCLD"); */
  register_signal(SIGCONT, "SIGCONT");
  register_signal(SIGFPE, "SIGFPE");
  register_signal(SIGHUP, "SIGHUP");
  register_signal(SIGILL, "SIGILL");
  register_signal(SIGINT, "SIGINT");
  register_signal(SIGIO, "SIGIO");
  /* register_signal(SIGIOT, "SIGIOT"); same as SIGABRT */
  register_signal(SIGPIPE, "SIGPIPE");
  /* register_signal(SIGPOLL, "SIGPOLL"); same as SIGIO*/
  register_signal(SIGPROF, "SIGPROF");
  register_signal(SIGPWR, "SIGPWR");
  register_signal(SIGQUIT, "SIGQUIT");
  register_signal(SIGSEGV, "SIGSEGV");
  register_signal(SIGSTKFLT, "SIGSTKFLT");
  /* register_signal(SIGSTOP, "SIGSTOP"); can't be caught*/
  register_signal(SIGSYS, "SIGSYS");
  register_signal(SIGTERM, "SIGTERM");
  register_signal(SIGTRAP, "SIGTRAP");
  register_signal(SIGTSTP, "SIGTSTP");
  register_signal(SIGTTIN, "SIGTTIN");
  register_signal(SIGTTOU, "SIGTTOU");
  /* register_signal(SIGUNUSED, "SIGUNUSED"); same as SIGSYS*/
  register_signal(SIGURG, "SIGURG");
  register_signal(SIGUSR1, "SIGUSR1");
  register_signal(SIGUSR2, "SIGUSR2");
  register_signal(SIGVTALRM, "SIGVTALRM");
  register_signal(SIGWINCH, "SIGWINCH");
  register_signal(SIGXCPU, "SIGXCPU");
  register_signal(SIGXFSZ, "SIGXFSZ");
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
      debug_print("child_died: %d\n", pid);
      return WEXITSTATUS(status);
    }
    if(DEBUG)  // will get optimized away by the compiler
      if(pid!=-1)  // ignore we might have no children in a suitable state
        debug_print("reaped_orphan: %d\n", pid);
  }
  return 256;
}

void execute(int argc, char** argv) {
  if (argc <= 1)
    return;
  char* cmd = argv[1];
  char** args = argv+1;
  debug_print("exec: %s\n", cmd);
  if (execvp(cmd, args) == -1) {
    fprintf(stderr, "failed to exec %s, errno is %d\n", cmd, errno);
  }
}

int main(int argc, char** argv) {
  debug_print("%s", "main\n");
  pid_t pid = fork();
  if (pid < 0) {
    fprintf(stderr, "failed to fork, errno: %d\n", errno);
    return EX_OSERR;
  } else if (pid > 0) {
    debug_print("child_pid: %d\n", pid);
    return pid_one(pid);
  } else if (pid == 0) {
    debug_print("fork=>0: %d\n", getpid());
    execute(argc, argv);
    return EX_OSERR; // program should have called exec and we should never get here
  }
  return 255; // if we reach this we messed up somehow
}
