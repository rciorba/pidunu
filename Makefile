all: build

build:
	-gcc -Wall -std=c99 -o grim *.c

.PHONY : clean
clean:
	-rm *.o
check-syntax:
	-gcc -Wall -std=c99 -o /dev/null  -S ${CHK_SOURCES}