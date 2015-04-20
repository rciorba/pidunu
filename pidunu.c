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
}

void reg_signal(int sig) {
  if (signal(sig, sig_handler) == SIG_ERR) {
    debug_print("failed to setup signal %d errno:%d", sig, errno);
    exit(-2);
  }
}

void setup_signals(pid_t child_pid) {
  g_child_pid = child_pid;
  // See signals in docker:
  // https://github.com/docker/docker/blob/487a417d9fd074d0e78876072c7d1ebfd398ea7a/pkg/signal/signal_linux.go
  // Can't register SIGKILL and SIGSTOP
  reg_signal(SIGABRT);
  reg_signal(SIGALRM);
  reg_signal(SIGBUS);
  reg_signal(SIGCHLD);
  reg_signal(SIGCLD);
  reg_signal(SIGCONT);
  reg_signal(SIGFPE);
  reg_signal(SIGHUP);
  reg_signal(SIGILL);
  reg_signal(SIGINT);
  reg_signal(SIGIO);
  reg_signal(SIGIOT);
  //reg_signal(SIGKILL);
  reg_signal(SIGPIPE);
  reg_signal(SIGPOLL);
  reg_signal(SIGPROF);
  reg_signal(SIGPWR);
  reg_signal(SIGQUIT);
  reg_signal(SIGSEGV);
  reg_signal(SIGSTKFLT);
  //reg_signal(SIGSTOP);
  reg_signal(SIGSYS);
  reg_signal(SIGTERM);
  reg_signal(SIGTRAP);
  reg_signal(SIGTSTP);
  reg_signal(SIGTTIN);
  reg_signal(SIGTTOU);
  reg_signal(SIGUNUSED);
  reg_signal(SIGURG);
  reg_signal(SIGUSR1);
  reg_signal(SIGUSR2);
  reg_signal(SIGVTALRM);
  reg_signal(SIGWINCH);
  reg_signal(SIGXCPU);
  reg_signal(SIGXFSZ);
}

int pid_one(pid_t child_pid) {
  int status, cstatus;
  pid_t pid;
  debug_print("%s\n", "pid_one");
  setup_signals(child_pid);

  while (1) {
    pid = wait(&status);
    if (pid < 0) {
      debug_print("wait error: %d / %d\n", pid, errno);
      return -1;
    }
    if (pid != 1) {
      debug_print("reaped_orphan:%d\n", pid);
    }
    // Stop the loop if the PID is the one of our child process
    if (pid == child_pid) {
      debug_print("child_pid exited: %d\n", status);
      cstatus = status;
      break;
    }
  }
  while ( (pid = waitpid(-1, NULL, WNOHANG)) >= 0) {
    // Reap potential other processes
    debug_print("reaped additional orphan:%d\n", pid);
  }
  // Return the child's process exit code
  debug_print("exit with statuscode: %d\n", WEXITSTATUS(cstatus));
  return WEXITSTATUS(cstatus);
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
