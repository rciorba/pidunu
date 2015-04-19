.PHONY : clean test

all: build

build:
	-gcc -Wall -std=c99 -o pidunu *.c -static

debug:
	-gcc -g -D_DEBUG -Wall -std=c99 -o pidunu_dbg *.c -static

test: debug
	py.test --capture=no test/

clean:
	-rm *.o

check-syntax:
	-gcc -Wall -std=c99 -o /dev/null  -S ${CHK_SOURCES}
