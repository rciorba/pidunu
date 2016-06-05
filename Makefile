.PHONY : clean test

all: build

build: pidunu

debug: pidunu_dbg

pidunu: pidunu.c
	-gcc -Wall -std=c99 -o pidunu pidunu.c -static

pidunu_dbg: pidunu.c
	-gcc -g -D_DEBUG -Wall -std=c99 -o pidunu_dbg pidunu.c -static

test: debug
	py.test -vv --capture=no test/

clean:
	-rm *.o

check-syntax:
	-gcc -Wall -std=c99 -o /dev/null -S ${CHK_SOURCES}
